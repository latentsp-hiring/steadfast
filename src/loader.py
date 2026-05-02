"""
Stage 1: Load data.

Reads the knowledge base CSV and the eval/custom ticket JSON,
returning normalised Ticket and KBEntry objects.
"""

from __future__ import annotations

import csv
import json
import logging
from collections import Counter
from pathlib import Path

from models import KBEntry, Ticket

logger = logging.getLogger(__name__)

# Column names expected in knowledge_base.csv
_KB_REQUIRED_COLS = {
    "ticket_id",
    "customer_name",
    "plan",
    "subject",
    "body",
    "category",
    "priority",
    "resolution",
}

# Keys expected in each ticket JSON object (eval set or custom input)
_TICKET_REQUIRED_KEYS = {"ticket_id", "subject", "body"}


def load_knowledge_base(path: str | Path) -> list[KBEntry]:
    """Parse the knowledge base CSV into a list of KBEntry objects.

    Rows with missing required columns are skipped with a warning.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Knowledge base not found: {path}")

    entries: list[KBEntry] = []
    skipped = 0

    with path.open(newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)

        missing = _KB_REQUIRED_COLS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(
                f"KB CSV is missing expected columns: {sorted(missing)}"
            )

        for i, row in enumerate(reader, start=2):  # row 1 is header
            if not all(row.get(c, "").strip() for c in ("ticket_id", "subject", "body")):
                logger.warning("KB row %d skipped — empty required field", i)
                skipped += 1
                continue

            entries.append(KBEntry(**{k: row.get(k, "") for k in _KB_REQUIRED_COLS}))

    logger.info("Loaded %d KB entries (%d skipped) from %s", len(entries), skipped, path)
    return entries


def load_tickets(path: str | Path) -> list[Ticket]:
    """Parse a ticket JSON file (eval set or custom input) into Ticket objects.

    Each JSON object must have at minimum: ticket_id, subject, body.
    Extra keys (customer_name, plan, expected_*) are read when present.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Ticket file not found: {path}")

    with path.open(encoding="utf-8") as fh:
        raw = json.load(fh)

    if not isinstance(raw, list):
        raise ValueError(f"Expected a JSON array in {path}, got {type(raw).__name__}")

    tickets: list[Ticket] = []
    skipped = 0

    for i, obj in enumerate(raw):
        missing = _TICKET_REQUIRED_KEYS - set(obj.keys())
        if missing:
            logger.warning(
                "Ticket #%d skipped — missing keys: %s", i, sorted(missing)
            )
            skipped += 1
            continue

        tickets.append(
            Ticket(
                ticket_id=obj["ticket_id"],
                customer_name=obj.get("customer_name", ""),
                plan=obj.get("plan", ""),
                subject=obj["subject"],
                body=obj["body"],
            )
        )

    logger.info("Loaded %d tickets (%d skipped) from %s", len(tickets), skipped, path)
    return tickets


def inspect_kb(entries: list[KBEntry]) -> dict:
    """Return a summary dict useful for data-exploration logging."""
    categories = Counter(e.category for e in entries)
    priorities = Counter(e.priority for e in entries)
    plans = Counter(e.plan for e in entries)

    if entries:
        body_lens = [len(e.body) for e in entries]
        res_lens = [len(e.resolution) for e in entries]
        avg_body_len = sum(body_lens) / len(body_lens)
        avg_res_len = sum(res_lens) / len(res_lens)
        body_min = min(body_lens)
        body_max = max(body_lens)
        res_min = min(res_lens)
        res_max = max(res_lens)
    else:
        avg_body_len = avg_res_len = 0.0
        body_min = body_max = res_min = res_max = 0

    return {
        "total_entries": len(entries),
        "category_distribution": dict(categories),
        "priority_distribution": dict(priorities),
        "plan_distribution": dict(plans),
        "avg_body_chars": round(avg_body_len),
        "min_body_chars": body_min,
        "max_body_chars": body_max,
        "avg_resolution_chars": round(avg_res_len),
        "min_resolution_chars": res_min,
        "max_resolution_chars": res_max,
    }
