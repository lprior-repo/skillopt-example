from __future__ import annotations

from skillopt.datasets.base import BatchSpec
from skillopt.envs.base import EnvAdapter
from skillopt.envs.holzman_rust.dataloader import HolzmanRustDataLoader
from skillopt.envs.holzman_rust.rollout import run_batch


class HolzmanRustAdapter(EnvAdapter):
    def __init__(
        self,
        split_dir: str = "",
        data_path: str = "",
        split_mode: str = "split_dir",
        split_ratio: str = "3:1:1",
        split_seed: int = 42,
        split_output_dir: str = "",
        workers: int = 1,
        analyst_workers: int = 2,
        failure_only: bool = False,
        minibatch_size: int = 4,
        edit_budget: int = 4,
        seed: int = 42,
        limit: int = 0,
        opencode_timeout: int = 900,
        cargo_timeout: int = 180,
        review_model: str = "",
        repair_model: str = "",
        opencode_variant: str = "",
        opencode_show_thinking: bool = False,
        references_dir: str = "",
        sandbox_root: str = "/tmp/opencode/holzman-skillopt",
        max_completion_tokens: int = 8192,
    ) -> None:
        self.workers = int(workers)
        self.analyst_workers = int(analyst_workers)
        self.failure_only = bool(failure_only)
        self.minibatch_size = int(minibatch_size)
        self.edit_budget = int(edit_budget)
        self.opencode_timeout = int(opencode_timeout)
        self.cargo_timeout = int(cargo_timeout)
        self.review_model = review_model
        self.repair_model = repair_model
        self.opencode_variant = opencode_variant
        self.opencode_show_thinking = bool(opencode_show_thinking)
        self.references_dir = references_dir
        self.sandbox_root = sandbox_root
        self.max_completion_tokens = int(max_completion_tokens)
        self.dataloader = HolzmanRustDataLoader(
            split_dir=split_dir,
            data_path=data_path,
            split_mode=split_mode,
            split_ratio=split_ratio,
            split_seed=split_seed,
            split_output_dir=split_output_dir,
            seed=seed,
            limit=limit,
        )

    def setup(self, cfg: dict) -> None:
        super().setup(cfg)
        self.dataloader.setup(cfg)
        self.references_dir = str(cfg.get("references_dir") or self.references_dir or "")
        target_model = str(cfg.get("target_model") or "").strip()
        self.review_model = str(cfg.get("review_model") or "").strip() or target_model or self.review_model
        self.repair_model = str(cfg.get("repair_model") or "").strip() or target_model or self.repair_model
        self.opencode_variant = str(cfg.get("opencode_variant") or self.opencode_variant or "").strip()
        self.opencode_show_thinking = bool(cfg.get("opencode_show_thinking") or self.opencode_show_thinking)
        self.sandbox_root = str(cfg.get("sandbox_root") or self.sandbox_root)
        self.opencode_timeout = int(cfg.get("opencode_timeout") or self.opencode_timeout)
        self.cargo_timeout = int(cfg.get("cargo_timeout") or self.cargo_timeout)

    def get_dataloader(self):
        return self.dataloader

    def build_env_from_batch(self, batch: BatchSpec, **kwargs):
        payload = batch.payload if isinstance(batch.payload, list) else []
        return list(payload)

    def build_train_env(self, batch_size: int, seed: int, **kwargs):
        batch = self.dataloader.build_train_batch(batch_size=batch_size, seed=seed, **kwargs)
        return self.build_env_from_batch(batch, **kwargs)

    def build_eval_env(self, env_num: int, split: str, seed: int, **kwargs):
        batch = self.dataloader.build_eval_batch(env_num=env_num, split=split, seed=seed, **kwargs)
        return self.build_env_from_batch(batch, **kwargs)

    def rollout(self, env_manager, skill_content: str, out_dir: str, **kwargs) -> list[dict]:
        return run_batch(
            items=list(env_manager),
            out_root=out_dir,
            skill_content=skill_content,
            references_dir=self.references_dir,
            review_model=self.review_model,
            repair_model=self.repair_model,
            opencode_variant=self.opencode_variant,
            opencode_show_thinking=self.opencode_show_thinking,
            workers=self.workers,
            opencode_timeout=self.opencode_timeout,
            cargo_timeout=self.cargo_timeout,
            sandbox_root=self.sandbox_root,
        )

    def get_task_types(self) -> list[str]:
        return ["review", "repair"]
