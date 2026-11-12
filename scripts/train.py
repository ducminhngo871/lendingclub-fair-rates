"""Step 2: train both scoring machines on the past, judge them on the future."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from lc_rates import config, data, features, finance, model  # noqa: E402


def main() -> None:
    df = data.load_clean()
    train, test = data.split_train_test(df)
    print(f"train {len(train):,} loans ({train.issue_year.min()}-{train.issue_year.max()}), "
          f"test {len(test):,} loans ({test.issue_year.min()}-{test.issue_year.max()})")

    X_train, X_test = features.build_features(train), features.build_features(test)
    y_train, y_test = train["defaulted"].to_numpy(), test["defaulted"].to_numpy()

    # Model 1: logistic regression
    logit = model.make_logistic().fit(X_train, y_train)
    p_logit = model.predict_pd(logit, X_test)

    # Model 2: LightGBM. Early stopping uses the last training year (2013) as validation,
    # then the model is refit on every training year with the chosen number of trees.
    fit_mask = (train["issue_year"] < config.VALID_YEAR).to_numpy()
    first = model.train_lgbm(X_train[fit_mask], y_train[fit_mask], X_train[~fit_mask], y_train[~fit_mask])
    best = int(first.best_iteration_ or first.n_estimators)
    lgbm = model.refit_lgbm(best, X_train, y_train)
    p_lgbm = model.predict_pd(lgbm, X_test)
    print(f"LightGBM: early stopping chose {best} trees")

    # Model 3: predicts each loan's *return* (used to pick the best loans to fund)
    ret_model, ret_trees = model.train_return_model(train)
    model.save_return_model(ret_model)
    print(f"Return model: {ret_trees} trees")

    # Benchmarks: LendingClub's own verdicts as risk scores
    scores = {
        "Logistic regression (mine)": p_logit,
        "LightGBM (mine)": p_lgbm,
        "LendingClub grade A-G": model.grade_to_score(test["grade"]).to_numpy(),
        "LendingClub sub-grade A1-G5": model.sub_grade_to_score(test["sub_grade"]).to_numpy(),
        "LendingClub interest rate": test["int_rate"].to_numpy(),
    }
    auc = model.score_summary(y_test, scores)
    print(auc.round(4).to_string(index=False))

    quality = pd.DataFrame(
        {"logistic": model.probability_quality(y_test, p_logit), "lightgbm": model.probability_quality(y_test, p_lgbm)}
    ).T

    lgd = finance.loss_given_default(train)
    grade_pd = (
        pd.DataFrame({"grade": test["grade"], "pd": p_lgbm}).groupby("grade")["pd"].mean().reindex(config.GRADES)
    )
    meta = {
        "feature_columns": features.FEATURE_COLUMNS,
        "lgd": lgd,
        "best_iteration": best,
        "train_years": [int(train.issue_year.min()), int(train.issue_year.max())],
        "test_years": list(config.TEST_YEARS),
        "grade_mean_model_pd": grade_pd.round(5).to_dict(),
        "grade_mean_interest_rate": (test.groupby("grade")["int_rate"].mean().reindex(config.GRADES) / 100).round(5).to_dict(),
        "test_auc": {k: float(v) for k, v in zip(auc["score"], auc["auc"])},
    }
    model.save_models(logit, lgbm, meta)

    config.RESULTS_DIR.mkdir(exist_ok=True)
    auc.to_csv(config.RESULTS_DIR / "auc_comparison.csv", index=False)
    quality.to_csv(config.RESULTS_DIR / "probability_quality.csv")
    np.save(config.PROCESSED_DIR / "test_pd_lgbm.npy", p_lgbm)
    np.save(config.PROCESSED_DIR / "test_pd_logistic.npy", p_logit)
    print(quality.round(4).to_string())
    print(f"LGD (train charged-off loans): {lgd:.3f}")
    print(json.dumps(meta["grade_mean_model_pd"]))


if __name__ == "__main__":
    main()
