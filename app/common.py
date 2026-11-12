"""Shared loading helpers for every page of the app."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from lc_rates import config, model  # noqa: E402

DATA = config.APP_DATA_DIR


@st.cache_resource
def models():
    return model.load_models()


@st.cache_data
def test_loans() -> pd.DataFrame:
    return pd.read_parquet(DATA / "test_loans.parquet")


@st.cache_data
def result(name: str) -> pd.DataFrame:
    return pd.read_csv(DATA / "results" / name)


@st.cache_data
def approval_cube() -> pd.DataFrame:
    return pd.read_parquet(DATA / "approval_cube.parquet")


def pct(x: float, digits: int = 1) -> str:
    return f"{x * 100:.{digits}f}%"
