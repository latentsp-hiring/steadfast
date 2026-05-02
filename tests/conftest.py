"""Shared fixtures for pipeline tests."""

from __future__ import annotations

from pathlib import Path

import pytest

# Project root (parent of tests/)
ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def data_dir() -> Path:
    return ROOT / "data"


@pytest.fixture
def sample_kb_path(data_dir: Path) -> Path:
    return data_dir / "knowledge_base.csv"


@pytest.fixture
def sample_eval_path(data_dir: Path) -> Path:
    return data_dir / "eval_set.json"
