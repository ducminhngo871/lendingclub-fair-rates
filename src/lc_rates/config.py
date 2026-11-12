"""Paths, column lists and the handful of numbers the whole project agrees on.

Everything a student might want to change (split year, fair-rate assumptions)
lives here so it is never hard-coded in two places.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
MODELS_DIR = ROOT / "models"
RESULTS_DIR = ROOT / "results"
FIGURES_DIR = RESULTS_DIR / "figures"
APP_DATA_DIR = ROOT / "app" / "data"

ACCEPTED_RAW = RAW_DIR / "accepted_2007_to_2018Q4.csv.gz"
REJECTED_RAW = RAW_DIR / "rejected_2007_to_2018Q4.csv.gz"
LOANS_CLEAN = PROCESSED_DIR / "loans_clean.parquet"

KAGGLE_DATASET = "wordsforthewise/lending-club"

# --- Which loans are usable -------------------------------------------------
# The Kaggle dump was taken at the end of 2018 (2018Q4). A loan is only
# "finished" if its last scheduled payment falls on or before that date.
# Without this rule, risky loans that have not had time to default yet make
# the data look safer than it is (the "right-censoring trap").
DATA_CUTOFF_YEAR = 2018
DATA_CUTOFF_MONTH = 12
FINISHED_STATUSES = {"Fully Paid": 0, "Charged Off": 1}

# --- Time split ---------------------------------------------------------------
# Train on the past, test on the future. Because of the maturity rule above,
# only 36-month loans issued by the end of 2015 survive in the test years.
TRAIN_END_YEAR = 2013
TEST_YEARS = (2014, 2015)
VALID_YEAR = 2013  # last training year, held out for LightGBM early stopping

# --- Columns ------------------------------------------------------------------
# Known when the loan is requested: safe to use as model inputs.
APPLICANT_COLUMNS = [
    "loan_amnt", "term", "emp_length", "home_ownership", "annual_inc", "purpose",
    "addr_state", "dti", "delinq_2yrs", "earliest_cr_line", "fico_range_low",
    "fico_range_high", "inq_last_6mths", "open_acc", "pub_rec", "revol_bal",
    "revol_util", "total_acc", "issue_d", "application_type",
]
# LendingClub's own verdict. Used ONLY as the benchmark, never as a model input.
LC_VERDICT_COLUMNS = ["grade", "sub_grade", "int_rate"]
# Only exist after the loan has run: used to measure outcomes, NEVER as inputs.
OUTCOME_COLUMNS = [
    "loan_status", "funded_amnt", "total_pymnt", "total_rec_prncp", "recoveries", "last_pymnt_d",
]
ACCEPTED_USECOLS = ["id", *APPLICANT_COLUMNS, *LC_VERDICT_COLUMNS, *OUTCOME_COLUMNS]

# `installment` is deliberately absent: it is computed from the interest rate,
# so using it would smuggle LendingClub's own price into the "independent" model.

PURPOSES = [
    "debt_consolidation", "credit_card", "home_improvement", "other",
    "major_purchase", "small_business", "car", "medical", "moving", "vacation",
    "house", "wedding", "renewable_energy", "educational",
]
HOME_OWNERSHIP = ["RENT", "MORTGAGE", "OWN", "OTHER"]
GRADES = list("ABCDEFG")

# --- Fair-rate assumptions (finance.py) -------------------------------------
# These are modelling choices, not facts. The app lets the user change them.
RISK_FREE_RATE = 0.02        # what a safe investment paid around 2014-15
REQUIRED_MARGIN = 0.02       # extra yearly return asked for illiquid consumer loans
# Loans amortise, so on average only about half the principal is outstanding.
# Losses measured against the funded amount therefore hit the *average balance*
# about twice as hard per year as a naive loss / term would suggest.
AVG_BALANCE_RATIO = 0.55
