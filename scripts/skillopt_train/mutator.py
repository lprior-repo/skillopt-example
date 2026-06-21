from __future__ import annotations

import hashlib
import json
import re
import shutil
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, TypedDict

from .errors import MutatorError, ProviderError
from .providers import ModelProvider, ModelRequest, extract_json
from .self_critique import CritiqueBlock
from .skill import Skill

_SLUG_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")

_DEFAULT_MAX_TOKENS: Final[int] = 4096
_DEFAULT_TEMPERATURE: Final[float] = 0.2
_MAX_SKILL_MD_CHARS: Final[int] = 8192
_MAX_PREVIOUS_ADDENDUM_CHARS: Final[int] = 4096
_DEFAULT_MAX_ADDENDUM_CHARS: Final[int] = 16384
_DEFAULT_MAX_ATTEMPTS: Final[int] = 3
_DEFAULT_FORBIDDEN_TOKENS: Final[tuple[str, ...]] = (
    "unsafe",
    "unwrap",
    "expect",
    "panic",
    "todo!",
    "unimplemented!",
    "unreachable!",
)
_RETRY_TAIL_LENGTH: Final[int] = 3


DEFAULT_PROMPT: Final[str] = """You are evolving a Rust skill called `holzman-rust`

Existing skill bundle (truncated):
```
{skill_md}
```

Previous candidate addendum (may be empty on first step):
```
{previous_addendum}
```

Self-critique from the previous step's grading report:
{critique}

Rules:
- Output a single JSON object: {{"addendum": "...", "reasoning": "..."}}
- The `addendum` is appended to the canonical SKILL.md
- It must be Markdown only
- Maximum length: {max_chars} characters
- Do NOT introduce these forbidden tokens in the addendum: {forbidden}
- Address the top failure modes listed in the self-critique
- Prefer concrete, testable rules over prose
- Cite specific gates (cargo fmt/clippy/test, audit, deny, vet, geiger, machete, mutants)
- If the critique is empty, propose the smallest change that strengthens the
  strongest existing rule in the skill bundle

Output ONLY the JSON object
No preamble, no explanation, no markdown headings
"""


class MutatorMetaDict(TypedDict):
    step: int
    candidate_name: str
    reasoning: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    attempts: list[str]
    created_at: float
    bundle_sha256: str


@dataclass(frozen=True, slots=True)
class MutatorMeta:
    step: int
    candidate_name: str
    reasoning: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    attempts: tuple[str, ...]
    created_at: float
    bundle_sha256: str

    def to_mapping(self) -> MutatorMetaDict:
        return {
            "step": self.step,
            "candidate_name": self.candidate_name,
            "reasoning": self.reasoning,
            "model": self.model,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": self.cost_usd,
            "attempts": list(self.attempts),
            "created_at": self.created_at,
            "bundle_sha256": self.bundle_sha256,
        }


@dataclass(frozen=True, slots=True)
class Mutator:
    provider: ModelProvider
    skill_root: Path
    candidate_root: Path
    base_overlay: Path
    prompt_template: str
    max_attempts: int
    forbidden_tokens: tuple[str, ...]

    @staticmethod
    def new(
        *,
        provider: ModelProvider,
        skill_root: Path,
        candidate_root: Path,
        base_overlay: Path,
        prompt_template: str = DEFAULT_PROMPT,
        max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
        forbidden_tokens: Sequence[str] = _DEFAULT_FORBIDDEN_TOKENS,
    ) -> Mutator:
        return Mutator(
            provider=provider,
            skill_root=skill_root,
            candidate_root=candidate_root,
            base_overlay=base_overlay,
            prompt_template=prompt_template,
            max_attempts=max(1, int(max_attempts)),
            forbidden_tokens=tuple(forbidden_tokens),
        )

    @staticmethod
    def from_skill(
        skill: Skill,
        provider: ModelProvider,
        *,
        candidate_root: Path,
        base_overlay: Path,
        max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
    ) -> Mutator:
        return Mutator(
            provider=provider,
            skill_root=skill.path,
            candidate_root=candidate_root,
            base_overlay=base_overlay,
            prompt_template=skill.load_prompt(),
            max_attempts=max(1, int(max_attempts)),
            forbidden_tokens=tuple(skill.rubric.forbidden_tokens),
        )

    def _safe_name(self, raw: str) -> str:
        candidate = raw.strip()
        if candidate == "baseline" or not _SLUG_RE.fullmatch(candidate):
            raise MutatorError(
                f"invalid candidate name: {raw!r}",
                code="bad_name",
                context={"name": raw},
            )
        return candidate

    def _read_skill_md(self) -> str:
        path = self.skill_root / "SKILL.md"
        return path.read_text(encoding="utf-8") if path.is_file() else ""

    def _build_prompt(
        self,
        *,
        previous_addendum: str,
        critique: CritiqueBlock | None,
        max_addendum_chars: int,
    ) -> str:
        skill_md = self._read_skill_md()
        ctx: dict[str, str] = {
            "skill_md": skill_md[:_MAX_SKILL_MD_CHARS],
            "previous_addendum": previous_addendum[:_MAX_PREVIOUS_ADDENDUM_CHARS],
            "critique": critique.prompt_section if critique else "(no prior critique)",
            "max_chars": str(max_addendum_chars),
            "forbidden": ", ".join(self.forbidden_tokens),
        }
        try:
            return self.prompt_template.format(**ctx)
        except (KeyError, IndexError) as exc:
            raise MutatorError(
                f"prompt template missing placeholder: {exc}",
                code="template_error",
                context={"placeholder": str(exc)},
            ) from exc

    def _request(self, prompt: str) -> ModelRequest:
        return ModelRequest.new(
            prompt=prompt,
            system="",
            max_tokens=_DEFAULT_MAX_TOKENS,
            temperature=_DEFAULT_TEMPERATURE,
            metadata={"workdir": str(self.candidate_root)},
        )

    def _validate_payload(
        self,
        payload: Mapping[str, object],
        *,
        max_chars: int,
    ) -> tuple[str, str]:
        addendum_raw = payload.get("addendum", "")
        if not isinstance(addendum_raw, str) or not addendum_raw.strip():
            raise MutatorError(
                "mutator response had empty addendum",
                code="empty_addendum",
            )
        addendum = addendum_raw.strip()
        if len(addendum) > max_chars:
            raise MutatorError(
                f"addendum too long: {len(addendum)} > {max_chars}",
                code="too_long",
                context={"chars": str(len(addendum)), "max": str(max_chars)},
            )
        lowered = addendum.lower()
        bad = [tok for tok in self.forbidden_tokens if tok in lowered]
        if bad:
            raise MutatorError(
                f"addendum contains forbidden tokens: {bad}",
                code="forbidden",
                context={"tokens": ",".join(bad)},
            )
        reasoning_raw = payload.get("reasoning", "")
        reasoning = reasoning_raw.strip() if isinstance(reasoning_raw, str) else ""
        return addendum, reasoning

    def propose(
        self,
        *,
        step: int,
        critique: CritiqueBlock | None = None,
        previous_addendum: str = "",
        max_addendum_chars: int = _DEFAULT_MAX_ADDENDUM_CHARS,
    ) -> tuple[Path, MutatorMeta]:
        candidate_name = self._safe_name(f"step-{step:03d}")
        target = self.candidate_root / candidate_name
        target.mkdir(parents=True, exist_ok=True)
        prompt = self._build_prompt(
            previous_addendum=previous_addendum,
            critique=critique,
            max_addendum_chars=max_addendum_chars,
        )
        attempts: list[str] = []
        last_exc: Exception | None = None
        response_model = ""
        usage_in = 0
        usage_out = 0
        cost = 0.0
        payload: Mapping[str, object] = {}
        for _ in range(self.max_attempts):
            try:
                response = self.provider.complete(self._request(prompt))
            except ProviderError as exc:
                last_exc = exc
                attempts.append(f"provider_error: {exc}")
                continue
            try:
                payload = extract_json(response.text)
            except (ProviderError, json.JSONDecodeError) as exc:
                last_exc = exc
                attempts.append(f"parse_error: {exc}")
                continue
            response_model = response.model
            usage_in = response.usage.input_tokens
            usage_out = response.usage.output_tokens
            cost = response.usage.cost_usd
            break
        else:
            raise MutatorError(
                f"mutator failed after {self.max_attempts} attempts: {last_exc}",
                code="exhausted",
                context={"attempts": "; ".join(attempts[-_RETRY_TAIL_LENGTH:])},
            ) from last_exc
        addendum, reasoning = self._validate_payload(payload, max_chars=max_addendum_chars)
        addendum_path = target / "SKILL-addendum.md"
        addendum_path.write_text(addendum.rstrip() + "\n", encoding="utf-8")
        refs_src = self.base_overlay / "references"
        refs_dst = target / "references"
        if refs_src.is_dir() and not refs_dst.exists():
            shutil.copytree(refs_src, refs_dst)
        meta = MutatorMeta(
            step=step,
            candidate_name=candidate_name,
            reasoning=reasoning,
            model=response_model,
            input_tokens=usage_in,
            output_tokens=usage_out,
            cost_usd=cost,
            attempts=tuple(attempts),
            created_at=time.time(),
            bundle_sha256=hash_overlay(target),
        )
        self._write_meta(target, meta)
        return target, meta

    def _write_meta(self, target: Path, meta: MutatorMeta) -> None:
        text = json.dumps(meta.to_mapping(), indent=2, sort_keys=True) + "\n"
        (target / "mutator.json").write_text(text, encoding="utf-8")


def propose(
    *,
    provider: ModelProvider,
    skill_root: Path,
    candidate_root: Path,
    base_overlay: Path,
    step: int,
    critique: CritiqueBlock | None = None,
    previous_addendum: str = "",
    prompt_template: str = DEFAULT_PROMPT,
    max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
    max_addendum_chars: int = _DEFAULT_MAX_ADDENDUM_CHARS,
) -> tuple[Path, MutatorMeta]:
    mutator = Mutator.new(
        provider=provider,
        skill_root=skill_root,
        candidate_root=candidate_root,
        base_overlay=base_overlay,
        prompt_template=prompt_template,
        max_attempts=max_attempts,
    )
    return mutator.propose(
        step=step,
        critique=critique,
        previous_addendum=previous_addendum,
        max_addendum_chars=max_addendum_chars,
    )


def propose_from_skill(
    skill: Skill,
    provider: ModelProvider,
    *,
    candidate_root: Path,
    base_overlay: Path,
    step: int,
    critique: CritiqueBlock | None = None,
    previous_addendum: str = "",
    max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
    max_addendum_chars: int = _DEFAULT_MAX_ADDENDUM_CHARS,
) -> tuple[Path, MutatorMeta]:
    mutator = Mutator.from_skill(
        skill=skill,
        provider=provider,
        candidate_root=candidate_root,
        base_overlay=base_overlay,
        max_attempts=max_attempts,
    )
    return mutator.propose(
        step=step,
        critique=critique,
        previous_addendum=previous_addendum,
        max_addendum_chars=max_addendum_chars,
    )


def hash_overlay(overlay: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(overlay.rglob("*")):
        if not path.is_file():
            continue
        digest.update(str(path.relative_to(overlay)).encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()
