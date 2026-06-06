"""
api_usage_tracker.py — Granular per-provider, per-model API token & cost tracking.

Tracks every call: provider, model, tokens in/out, estimated cost, timestamp.
Persists to /root/Geeves/data/api_usage.jsonl (one JSON line per call).

Usage:
    from lib.api_usage_tracker import ApiTracker

    tracker = ApiTracker()
    tracker.log(provider="openrouter", model="openrouter/owl-alpha",
                tokens_in=150, tokens_out=300, cost=0.0012)

    print(tracker.summary())          # human-readable summary
    print(tracker.totals_by_provider())  # dict of provider -> {calls, tokens, cost}
"""

from __future__ import annotations

import json
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Default data file
DATA_DIR = Path("/root/Geeves/data")
USAGE_FILE = DATA_DIR / "api_usage.jsonl"

# Approximate cost-per-1K-token (USD) — update these as pricing changes
MODEL_COSTS: dict[str, tuple[float, float]] = {
    # model:                 (input_cost_per_1k, output_cost_per_1k)
    "openrouter/owl-alpha":  (0.0002, 0.0004),
    "llama-3.3-70b-versatile": (0.00059, 0.00077),
    "llama-3.1-8b-instant":  (0.00005, 0.00008),
    "meta/llama-3.1-70b-instruct": (0.0004, 0.0004),
    "meta/llama-3.1-8b-instruct":  (0.00005, 0.00005),
    "qwen2.5:7b":            (0.0, 0.0),     # local — free
    "llama3.1:8b":           (0.0, 0.0),
    "mistral:7b":            (0.0, 0.0),
}


# ---------------------------------------------------------------------------
# ApiTracker
# ---------------------------------------------------------------------------

@dataclass
class ApiTracker:
    """Append-only usage tracker backed by a JSONL file."""

    data_file: Path = field(default=USAGE_FILE)
    _records: list[dict[str, Any]] = field(default_factory=list, repr=False)

    def __post_init__(self) -> None:
        self.data_file = Path(self.data_file)
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        if self.data_file.exists():
            self._records = self._load()

    # ---- public API -------------------------------------------------------

    def log(
        self,
        provider: str,
        model: str,
        tokens_in: int,
        tokens_out: int,
        cost: Optional[float] = None,
        meta: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Record one API call.  If cost is None, estimates from MODEL_COSTS.
        Returns the record that was written.
        """
        if cost is None:
            cost = self._estimate_cost(model, tokens_in, tokens_out)

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "provider": provider,
            "model": model,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "tokens_total": tokens_in + tokens_out,
            "cost_usd": round(cost, 6),
            "meta": meta or {},
        }

        # Append to file
        with open(self.data_file, "a") as f:
            f.write(json.dumps(record) + "\n")

        self._records.append(record)
        logger.debug("Logged: %s %s in=%d out=%d $%.6f",
                      provider, model, tokens_in, tokens_out, cost)
        return record

    def totals_by_provider(self) -> dict[str, dict[str, Any]]:
        """Aggregate totals grouped by provider."""
        totals: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"calls": 0, "tokens_in": 0, "tokens_out": 0,
                     "tokens_total": 0, "cost_usd": 0.0, "models": set()}
        )
        for r in self._records:
            t = totals[r["provider"]]
            t["calls"] += 1
            t["tokens_in"] += r["tokens_in"]
            t["tokens_out"] += r["tokens_out"]
            t["tokens_total"] += r.get("tokens_total", r["tokens_in"] + r["tokens_out"])
            t["cost_usd"] += r["cost_usd"]
            t["models"].add(r["model"])
        # Convert sets to sorted lists for JSON serializability
        for v in totals.values():
            v["models"] = sorted(v["models"])
            v["cost_usd"] = round(v["cost_usd"], 6)
        return dict(totals)

    def totals_by_model(self) -> dict[str, dict[str, Any]]:
        """Aggregate totals grouped by model."""
        totals: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"calls": 0, "tokens_in": 0, "tokens_out": 0,
                     "tokens_total": 0, "cost_usd": 0.0, "providers": set()}
        )
        for r in self._records:
            t = totals[r["model"]]
            t["calls"] += 1
            t["tokens_in"] += r["tokens_in"]
            t["tokens_out"] += r["tokens_out"]
            t["tokens_total"] += r.get("tokens_total", r["tokens_in"] + r["tokens_out"])
            t["cost_usd"] += r["cost_usd"]
            t["providers"].add(r["provider"])
        for v in totals.values():
            v["providers"] = sorted(v["providers"])
            v["cost_usd"] = round(v["cost_usd"], 6)
        return dict(totals)

    def summary(self) -> str:
        """Human-readable multi-line summary."""
        by_provider = self.totals_by_provider()
        total_calls = sum(v["calls"] for v in by_provider.values())
        total_tokens = sum(v["tokens_total"] for v in by_provider.values())
        total_cost = sum(v["cost_usd"] for v in by_provider.values())

        lines = [
            "═" * 55,
            "  API Usage Summary",
            "═" * 55,
            f"  Total calls:   {total_calls}",
            f"  Total tokens:  {total_tokens:,}",
            f"  Total cost:    ${total_cost:.4f}",
            "─" * 55,
        ]
        for prov, v in sorted(by_provider.items()):
            lines.append(f"  {prov}:")
            lines.append(f"    Calls:   {v['calls']}")
            lines.append(f"    Tokens:  {v['tokens_total']:,}")
            lines.append(f"    Cost:    ${v['cost_usd']:.4f}")
            lines.append(f"    Models:  {', '.join(v['models'])}")
        lines.append("═" * 55)
        return "\n".join(lines)

    def recent(self, n: int = 10) -> list[dict[str, Any]]:
        """Return the last N records (most recent first)."""
        return list(reversed(self._records[-n:]))

    def filter_by(self, provider: Optional[str] = None,
                  model: Optional[str] = None,
                  since: Optional[str] = None) -> list[dict[str, Any]]:
        """Filter records by provider, model, or ISO timestamp >= since."""
        results = self._records
        if provider:
            results = [r for r in results if r["provider"] == provider]
        if model:
            results = [r for r in results if r["model"] == model]
        if since:
            results = [r for r in results if r["timestamp"] >= since]
        return results

    # ---- internals --------------------------------------------------------

    def _load(self) -> list[dict[str, Any]]:
        records = []
        for line in self.data_file.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return records

    @staticmethod
    def _estimate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
        inp_rate, out_rate = MODEL_COSTS.get(model, (0.0, 0.0))
        return (tokens_in / 1000) * inp_rate + (tokens_out / 1000) * out_rate


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------

def log_call(provider: str, model: str, tokens_in: int, tokens_out: int,
             cost: Optional[float] = None,
             meta: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """One-liner to log a call without creating a tracker manually."""
    return ApiTracker().log(provider, model, tokens_in, tokens_out, cost=cost, meta=meta)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tracker = ApiTracker()
    print(tracker.summary())

    recent = tracker.recent(5)
    if recent:
        print("\nRecent calls:")
        for r in recent:
            print(f"  {r['timestamp'][:19]}  {r['provider']:12s}  "
                  f"{r['model']:35s}  in={r['tokens_in']:5d}  "
                  f"out={r['tokens_out']:5d}  ${r['cost_usd']:.6f}")
