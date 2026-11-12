"""The two "scoring machines" plus the tools to judge them."""

from __future__ import annotations

import json

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier, early_stopping, log_evaluation
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from . import config, features


def make_logistic(C: float = 0.5) -> Pipeline:
    """Model 1: easy to explain. Each coefficient says how a factor moves risk."""
    pre = ColumnTransformer(
        [
            (
                "num",
                Pipeline(
                    [("impute", SimpleImputer(strategy="median", add_indicator=True)), ("scale", StandardScaler())]
                ),
                features.NUMERIC_FEATURES,
            ),
            ("cat", OneHotEncoder(handle_unknown="ignore"), features.CATEGORICAL_FEATURES),
        ]
    )
    return Pipeline([("pre", pre), ("clf", LogisticRegression(C=C, max_iter=2000))])


def train_lgbm(
    X_fit: pd.DataFrame, y_fit, X_val: pd.DataFrame, y_val, *, params: dict | None = None
) -> LGBMClassifier:
    """Model 2: stronger. Early stopping on a held-out *later* year prevents memorising."""
    base = dict(
        n_estimators=3000, learning_rate=0.05, num_leaves=31, min_child_samples=200,
        subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=5.0,
        random_state=0, verbose=-1,
    )
    base.update(params or {})
    model = LGBMClassifier(**base)
    model.fit(
        X_fit, y_fit, eval_set=[(X_val, y_val)], eval_metric="auc",
        callbacks=[early_stopping(100, verbose=False), log_evaluation(0)],
    )
    return model


def refit_lgbm(best_iteration: int, X: pd.DataFrame, y, *, params: dict | None = None) -> LGBMClassifier:
    """Refit on all training years using the number of trees early stopping chose."""
    base = dict(
        n_estimators=best_iteration, learning_rate=0.05, num_leaves=31, min_child_samples=200,
        subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=5.0,
        random_state=0, verbose=-1,
    )
    base.update(params or {})
    return LGBMClassifier(**base).fit(X, y)


def predict_pd(model, X: pd.DataFrame) -> np.ndarray:
    return model.predict_proba(X)[:, 1]


# --- Judging -------------------------------------------------------------------
def grade_to_score(grade: pd.Series) -> pd.Series:
    """A=0 (safest) ... G=6 (riskiest), so a grade can be scored by AUC like a model."""
    return grade.map({g: i for i, g in enumerate(config.GRADES)}).astype(float)


def sub_grade_to_score(sub_grade: pd.Series) -> pd.Series:
    """A1=0 ... G5=34."""
    order = {f"{g}{n}": i * 5 + (n - 1) for i, g in enumerate(config.GRADES) for n in range(1, 6)}
    return sub_grade.map(order).astype(float)


def score_summary(y, scores: dict[str, np.ndarray]) -> pd.DataFrame:
    """AUC for any number of risk scores (higher score = riskier)."""
    rows = [{"score": name, "auc": roc_auc_score(y, s)} for name, s in scores.items()]
    return pd.DataFrame(rows).sort_values("auc", ascending=False).reset_index(drop=True)


def probability_quality(y, p) -> dict[str, float]:
    """How trustworthy the *probabilities* are, not just the ranking."""
    p = np.clip(p, 1e-6, 1 - 1e-6)
    return {
        "auc": roc_auc_score(y, p),
        "brier": brier_score_loss(y, p),
        "log_loss": log_loss(y, p),
        "mean_predicted": float(np.mean(p)),
        "actual_default_rate": float(np.mean(y)),
    }


def decile_table(y, p, n: int = 10) -> pd.DataFrame:
    """Split borrowers into equal-sized groups by model risk; compare predicted vs actual."""
    df = pd.DataFrame({"y": np.asarray(y), "p": np.asarray(p)})
    df["decile"] = pd.qcut(df["p"].rank(method="first"), n, labels=range(1, n + 1))
    t = df.groupby("decile", observed=True).agg(
        loans=("y", "size"), mean_predicted_pd=("p", "mean"), actual_default_rate=("y", "mean")
    )
    return t.reset_index()


def disagreement_table(test: pd.DataFrame, model_pd: np.ndarray, quantile: float = 0.3) -> pd.DataFrame:
    """Where do the model and LendingClub disagree, and who turned out right?

    Both are turned into percentile ranks of risk (0 = safest). A loan is in a
    disagreement group when one side puts it in the safest 30% and the other in the
    riskiest 30%.
    """
    lc_rank = sub_grade_to_score(test["sub_grade"]).rank(pct=True, method="average")
    m_rank = pd.Series(model_pd, index=test.index).rank(pct=True, method="average")
    y = test["defaulted"]
    groups = {
        "LC says safe, model says risky": (lc_rank <= quantile) & (m_rank >= 1 - quantile),
        "LC says risky, model says safe": (lc_rank >= 1 - quantile) & (m_rank <= quantile),
        "Both say safe": (lc_rank <= quantile) & (m_rank <= quantile),
        "Both say risky": (lc_rank >= 1 - quantile) & (m_rank >= 1 - quantile),
    }
    rows = []
    for name, mask in groups.items():
        rows.append(
            {
                "group": name,
                "loans": int(mask.sum()),
                "actual_default_rate": float(y[mask].mean()) if mask.any() else np.nan,
                "mean_interest_rate": float(test.loc[mask, "int_rate"].mean() / 100) if mask.any() else np.nan,
                "mean_model_pd": float(model_pd[mask.to_numpy()].mean()) if mask.any() else np.nan,
            }
        )
    return pd.DataFrame(rows)


def shap_importance(model: LGBMClassifier, X: pd.DataFrame, sample: int = 20000, seed: int = 0):
    """Mean |SHAP| per feature on a random sample. Returns (importance table, shap values, sample)."""
    import shap

    Xs = X.sample(min(sample, len(X)), random_state=seed)
    values = shap.TreeExplainer(model).shap_values(Xs)
    if isinstance(values, list):  # older shap versions return one array per class
        values = values[1]
    imp = (
        pd.DataFrame({"feature": Xs.columns, "mean_abs_shap": np.abs(values).mean(axis=0)})
        .sort_values("mean_abs_shap", ascending=False)
        .reset_index(drop=True)
    )
    return imp, values, Xs


def logistic_coefficients(pipe: Pipeline) -> pd.DataFrame:
    """Readable coefficient table (odds-ratio per 1 std for numeric features)."""
    names = pipe.named_steps["pre"].get_feature_names_out()
    coef = pipe.named_steps["clf"].coef_[0]
    t = pd.DataFrame({"feature": names, "coef": coef, "odds_ratio": np.exp(coef)})
    return t.reindex(t["coef"].abs().sort_values(ascending=False).index).reset_index(drop=True)


# --- Saving --------------------------------------------------------------------
def save_models(logistic, lgbm, meta: dict) -> None:
    config.MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump(logistic, config.MODELS_DIR / "logistic.joblib", compress=3)
    joblib.dump(lgbm, config.MODELS_DIR / "lgbm.joblib", compress=3)
    (config.MODELS_DIR / "meta.json").write_text(json.dumps(meta, indent=2))


def save_return_model(m) -> None:
    config.MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump(m, config.MODELS_DIR / "return_lgbm.joblib", compress=3)


def load_return_model():
    return joblib.load(config.MODELS_DIR / "return_lgbm.joblib")


def load_models():
    logistic = joblib.load(config.MODELS_DIR / "logistic.joblib")
    lgbm = joblib.load(config.MODELS_DIR / "lgbm.joblib")
    meta = json.loads((config.MODELS_DIR / "meta.json").read_text())
    return logistic, lgbm, meta


# --- Picking loans for return (investor model) ---------------------------------------
def return_features(df: pd.DataFrame) -> pd.DataFrame:
    """Everything an investor can see before funding: the borrower inputs plus LendingClub's
    own grade and rate (they are shown to investors, so using them here is fair)."""
    X = features.build_features(df)
    X["int_rate"] = df["int_rate"].to_numpy()
    X["sub_grade_score"] = sub_grade_to_score(df["sub_grade"]).to_numpy()
    return X


def return_target(df: pd.DataFrame) -> pd.Series:
    """Total return per year of loan term: (cash back - cash lent) / cash lent / years."""
    return (df["total_pymnt"] - df["funded_amnt"]) / df["funded_amnt"] / (df["term_months"] / 12)


def train_return_model(train: pd.DataFrame, n_estimators: int | None = None, valid_year: int = config.VALID_YEAR):
    """LightGBM regressor of per-loan return. With no n_estimators, early-stops on `valid_year`
    (the last training year by default); returns (model, trees used)."""
    from lightgbm import LGBMRegressor

    X, y = return_features(train), return_target(train)
    base = dict(learning_rate=0.03, num_leaves=15, min_child_samples=500, subsample=0.8, subsample_freq=1,
                colsample_bytree=0.8, reg_lambda=10.0, random_state=0, verbose=-1)
    if n_estimators is None:
        fit = (train["issue_year"] < valid_year).to_numpy()
        m = LGBMRegressor(n_estimators=2000, **base).fit(
            X[fit], y[fit], eval_set=[(X[~fit], y[~fit])], callbacks=[early_stopping(100, verbose=False)]
        )
        return m, int(m.best_iteration_ or 2000)
    return LGBMRegressor(n_estimators=n_estimators, **base).fit(X, y), n_estimators
