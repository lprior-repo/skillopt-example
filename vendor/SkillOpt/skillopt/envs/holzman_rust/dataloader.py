from __future__ import annotations

import json
from pathlib import Path

from skillopt.datasets.base import SplitDataLoader


def _normalize_item(raw: dict) -> dict:
    item_id = str(raw.get("id") or "")
    kind = str(raw.get("kind") or raw.get("task_type") or "review")
    return {
        **raw,
        "id": item_id,
        "kind": kind,
        "task_type": kind,
        "task_description": str(raw.get("description") or item_id),
    }


class HolzmanRustDataLoader(SplitDataLoader):
    def load_split_items(self, split_path: str) -> list[dict]:
        path = Path(split_path)
        candidates = [path / "items.json", path / "tasks.json", path / "items.jsonl"]
        for candidate in candidates:
            if not candidate.exists():
                continue
            if candidate.suffix == ".jsonl":
                items: list[dict] = []
                with candidate.open("r", encoding="utf-8") as handle:
                    for line in handle:
                        stripped = line.strip()
                        if stripped:
                            items.append(_normalize_item(json.loads(stripped)))
                return items
            payload = json.loads(candidate.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                payload = payload.get("tasks") or payload.get("items") or payload.get("data") or []
            if not isinstance(payload, list):
                raise ValueError(f"Expected list-like payload in {candidate}")
            return [_normalize_item(item) for item in payload]
        raise FileNotFoundError(f"No items.json or items.jsonl found in {split_path}")

    def load_raw_items(self, data_path: str) -> list[dict]:
        path = Path(data_path)
        if path.is_dir():
            for name in ("items.json", "tasks.json"):
                candidate = path / name
                if candidate.exists():
                    path = candidate
                    break
            else:
                raise FileNotFoundError(f"No items.json or tasks.json found in {data_path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload = payload.get("tasks") or payload.get("items") or payload.get("data") or []
        if not isinstance(payload, list):
            raise ValueError(f"Expected list-like payload in {path}")
        return [_normalize_item(item) for item in payload]
