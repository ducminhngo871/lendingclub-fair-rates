"""Step 4: gather everything the web app needs into app/data/ (small files, safe to commit)."""

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


from lc_rates import config, data, features, model  # noqa: E402

RESULT_FILES = [
    "auc_comparison.csv", "probability_quality.csv", "decile_table_lgbm.csv", "disagreements.csv",
    "incremental_information.csv", "investment_strategies.csv", "investment_share_sweep.csv",
    "grade_economics.csv", "fair_rate_gaps.csv", "shap_importance.csv", "approval_by_risk_bin.csv",
    "approval_by_dti_bin.csv",
]


def main() -> None:
    out = config.APP_DATA_DIR
    (out / "results").mkdir(parents=True, exist_ok=True)

    _, test = data.split_train_test(data.load_clean())
    _, lgbm, _ = model.load_models()
    X = features.build_features(test)
    test_loans = test[[
        "grade", "sub_grade", "int_rate", "defaulted", "total_pymnt", "funded_amnt", "term_months", "months_paid",
        "fico_mid", "purpose", "home_ownership", "dti", "annual_inc", "loan_amnt", "addr_state", "issue_year",
    ]].copy()
    test_loans["model_pd"] = model.predict_pd(lgbm, X).astype("float32")
    test_loans["pred_return"] = model.load_return_model().predict(model.return_features(test)).astype("float32")
    for c in ("grade", "sub_grade", "purpose", "home_ownership", "addr_state"):
        test_loans[c] = test_loans[c].astype("category")
    for c in test_loans.select_dtypes("float64").columns:
        test_loans[c] = test_loans[c].astype("float32")
    test_loans.to_parquet(out / "test_loans.parquet", index=False)

    for f in RESULT_FILES:
        shutil.copy(config.RESULTS_DIR / f, out / "results" / f)
    print(f"app/data ready: {len(test_loans):,} test loans, {len(RESULT_FILES)} result tables")


if __name__ == "__main__":
    main()
