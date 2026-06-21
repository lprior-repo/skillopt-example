from __future__ import annotations

import os
import shutil
import subprocess
from collections.abc import Mapping
from pathlib import Path
from typing import Final

from ..errors import ProviderError
from .base import ModelRequest, ModelResponse, now_ms, parse_usage_block

_DEFAULT_WORKDIR: Final[str] = "/tmp/opencode/skillopt-train"
_OPENCODE_BIN: Final[str] = "opencode"
_DISABLED_SKILLS_ENV: Final[str] = '{"lsp": false}'
_STDERR_PREVIEW_CHARS: Final[int] = 512


class OpencodeProvider:
    name: str
    _model: str
    _timeout: int

    def __init__(self, model: str = "opencode default", timeout: int = 900) -> None:
        if not shutil.which(_OPENCODE_BIN):
            raise ProviderError(
                f"{_OPENCODE_BIN} binary not found on PATH",
                code="binary_missing",
                context={"binary": _OPENCODE_BIN},
            )
        self.name = "opencode"
        self._model = model
        self._timeout = max(30, int(timeout))

    @property
    def model(self) -> str:
        return self._model

    @staticmethod
    def _build_args(request: ModelRequest, model: str, workdir: Path) -> list[str]:
        args: list[str] = [
            _OPENCODE_BIN,
            "run",
            "--pure",
            "--dir",
            str(workdir),
            "--agent",
            "build",
            "--dangerously-skip-permissions",
            "--title",
            f"skillopt-train-{now_ms()}",
        ]
        chosen_model = request.model or model
        if chosen_model:
            args.extend(["--model", chosen_model])
        if request.system:
            args.extend(["--system", request.system])
        args.append(request.prompt)
        return args

    @staticmethod
    def _isolated_env() -> Mapping[str, str]:
        env: dict[str, str] = dict(os.environ)
        env["OPENCODE_DISABLE_EXTERNAL_SKILLS"] = "1"
        env["OPENCODE_DISABLE_CLAUDE_CODE_SKILLS"] = "1"
        env["OPENCODE_DISABLE_DEFAULT_PLUGINS"] = "1"
        env["OPENCODE_CONFIG_CONTENT"] = _DISABLED_SKILLS_ENV
        return env

    def complete(self, request: ModelRequest) -> ModelResponse:
        workdir = Path(request.metadata.get("workdir", _DEFAULT_WORKDIR))
        workdir.mkdir(parents=True, exist_ok=True)
        args = self._build_args(request, self._model, workdir)
        started = now_ms()
        try:
            proc = subprocess.run(
                args,
                cwd=workdir,
                env=self._isolated_env(),
                text=True,
                capture_output=True,
                check=False,
                timeout=self._timeout,
            )
        except subprocess.TimeoutExpired as exc:
            raise ProviderError(
                f"{_OPENCODE_BIN} run timed out after {self._timeout}s",
                code="timeout",
                context={"timeout": str(self._timeout)},
            ) from exc
        latency = now_ms() - started
        stderr = proc.stderr or ""
        stdout = proc.stdout or ""
        usage = parse_usage_block(stdout, stderr)
        if proc.returncode != 0:
            raise ProviderError(
                f"{_OPENCODE_BIN} run failed rc={proc.returncode}",
                code="nonzero_exit",
                context={
                    "returncode": str(proc.returncode),
                    "stderr": stderr[:_STDERR_PREVIEW_CHARS],
                },
            )
        return ModelResponse(
            text=stdout.strip(),
            usage=usage,
            model=request.model or self._model,
            latency_ms=latency,
            raw={"returncode": proc.returncode, "stderr": stderr[:_STDERR_PREVIEW_CHARS]},
        )

    def health(self) -> Mapping[str, str]:
        return {"provider": self.name, "model": self._model, "timeout": str(self._timeout)}
