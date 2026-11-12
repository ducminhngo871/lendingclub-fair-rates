"""Every page must open and render without an exception (needs the files in app/data)."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / "app"
PAGES = [APP / "streamlit_app.py", *sorted((APP / "pages").glob("*.py"))]

pytestmark = pytest.mark.skipif(not (APP / "data" / "test_loans.parquet").exists(), reason="run scripts/build_app_data.py first")


@pytest.mark.parametrize("page", PAGES, ids=lambda p: p.name)
def test_page_renders(page):
    at = AppTest.from_file(str(page), default_timeout=120).run()
    assert not at.exception, [e.value for e in at.exception]


def test_loan_pricing_risk_rises_when_the_borrower_looks_worse():
    at = AppTest.from_file(str(APP / "pages" / "1_Loan_pricing.py"), default_timeout=120).run()
    good = float(at.metric[0].value.rstrip("%"))
    # worse borrower: low score, high debt load
    for s in at.slider:
        if s.label.startswith("Credit score"):
            s.set_value(620)
        if s.label.startswith("Debt-to-income"):
            s.set_value(40.0)
    at.button[0].click().run()  # form values only count once the form is submitted
    assert float(at.metric[0].value.rstrip("%")) > good
