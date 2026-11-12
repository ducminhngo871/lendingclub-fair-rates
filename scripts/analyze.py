"""Step 3: every table and figure the report needs, written to results/.

Run after prepare_data.py, train.py and build_rejected.py.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.metrics import roc_auc_score  # noqa: E402
from sklearn.model_selection import cross_val_predict  # noqa: E402

from lc_rates import config, data, features, finance, model, rejected  # noqa: E402

BLUE, RED, GREY, GREEN = "#2b6cb0", "#c53030", "#718096", "#2f855a"
plt.rcParams.update(
    {"figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
     "grid.alpha": 0.25, "axes.axisbelow": True, "font.size": 10}
)


def save(fig, name: str) -> None:
    config.FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(config.FIGURES_DIR / f"{name}.png")
    plt.close(fig)


def pct(ax, axis="y") -> None:
    a = ax.yaxis if axis == "y" else ax.xaxis
    a.set_major_locator(matplotlib.ticker.MaxNLocator(nbins=6, steps=[1, 2, 5, 10]))
    a.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))


# ---------------------------------------------------------------------------------
def eda(df: pd.DataFrame) -> None:
    """Week 3: who defaults? One table + one chart per factor."""
    d = df.assign(
        fico_band=pd.cut(df["fico_mid"], [0, 680, 700, 720, 740, 760, 900], right=False,
                         labels=["<680", "680-699", "700-719", "720-739", "740-759", "760+"]),
        income_quartile=pd.qcut(df["annual_inc"], 4, labels=["Q1 (lowest)", "Q2", "Q3", "Q4 (highest)"]),
        dti_band=pd.cut(df["dti"].clip(0, 60), [-1, 10, 20, 30, 60], labels=["0-10", "10-20", "20-30", "30+"]),
    )
    factors = {"grade": "LendingClub grade", "issue_year": "year issued", "purpose": "loan purpose",
               "fico_band": "FICO band", "income_quartile": "income quartile", "dti_band": "debt-to-income (%)",
               "term_months": "term (months)"}
    base = d["defaulted"].mean()
    fig, axes = plt.subplots(2, 4, figsize=(17, 7.5))
    for ax, (col, label) in zip(axes.ravel(), factors.items()):
        t = d.groupby(col, observed=True)["defaulted"].agg(["mean", "size"]).reset_index()
        t.to_csv(config.RESULTS_DIR / f"eda_default_by_{col}.csv", index=False)
        ax.bar(t[col].astype(str), t["mean"], color=BLUE)
        ax.axhline(base, color=RED, ls="--", lw=1)
        ax.set_title(f"Default rate by {label}", fontsize=10)
        ax.tick_params(axis="x", rotation=90 if col == "purpose" else 0, labelsize=8)
        pct(ax)
    axes.ravel()[-1].axis("off")
    axes.ravel()[-1].text(0, 0.5, f"Dashed line = overall default\nrate {base:.1%}\n({len(d):,} finished, matured loans)", va="center")
    save(fig, "01_default_rate_by_factor")


def grade_view(test: pd.DataFrame, lgd: float) -> pd.DataFrame:
    """Does the interest each grade pays cover the money it loses?"""
    t = finance.grade_economics(test, lgd)
    t.to_csv(config.RESULTS_DIR / "grade_economics.csv", index=False)
    x = np.arange(len(t))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(x - 0.27, t["mean_interest_rate"], 0.27, label="Interest rate charged", color=BLUE)
    ax.bar(x, t["expected_loss_share"], 0.27, label="Money lost to defaults (share of loan)", color=RED)
    ax.bar(x + 0.27, t["realised_annual_return"], 0.27, label="Lender's actual yearly return (IRR)", color=GREEN)
    ax.axhline(config.RISK_FREE_RATE, color=GREY, ls=":", lw=1.2)
    ax.text(len(t) - 0.5, config.RISK_FREE_RATE + 0.004, "risk-free 2%", ha="right", color=GREY, fontsize=8)
    ax.set_xticks(x, t["grade"])
    ax.set_title("2014-15 loans by grade: interest charged vs what lenders really kept")
    ax.legend(frameon=False, fontsize=8)
    pct(ax)
    save(fig, "02_grade_economics")
    return t


def compare_with_lc(test: pd.DataFrame, p_logit, p_lgbm) -> None:
    y = test["defaulted"].to_numpy()
    auc = pd.read_csv(config.RESULTS_DIR / "auc_comparison.csv")

    fig, ax = plt.subplots(figsize=(8, 3.8))
    colors = [BLUE if "mine" in s else GREY for s in auc["score"]]
    ax.barh(auc["score"][::-1], auc["auc"][::-1], color=colors[::-1])
    ax.set_xlim(0.5, auc["auc"].max() + 0.03)
    ax.set_title("Ranking power on 2014-15 loans (AUC, higher is better; 0.5 = coin flip)")
    for i, v in enumerate(auc["auc"][::-1]):
        ax.text(v + 0.001, i, f"{v:.3f}", va="center", fontsize=9)
    save(fig, "03_auc_comparison")

    # calibration: when the model says X%, how often does it happen?
    fig, ax = plt.subplots(figsize=(5.5, 5))
    for name, p, c in (("LightGBM", p_lgbm, BLUE), ("Logistic", p_logit, GREEN)):
        t = model.decile_table(y, p)
        ax.plot(t["mean_predicted_pd"], t["actual_default_rate"], "o-", color=c, label=name)
        if name == "LightGBM":
            t.to_csv(config.RESULTS_DIR / "decile_table_lgbm.csv", index=False)
    lim = [0, 0.4]
    ax.plot(lim, lim, "--", color=GREY, label="perfect")
    ax.set_xlabel("Predicted default probability (decile average)")
    ax.set_ylabel("Actual default rate")
    ax.set_title("Calibration on 2014-15 loans")
    ax.legend(frameon=False)
    pct(ax)
    pct(ax, "x")
    save(fig, "04_calibration")

    dis = model.disagreement_table(test, p_lgbm)
    dis.to_csv(config.RESULTS_DIR / "disagreements.csv", index=False)

    # Does my model know something the LendingClub grade does not?
    lc = model.sub_grade_to_score(test["sub_grade"]).to_numpy()
    logit_p = np.log(np.clip(p_lgbm, 1e-4, 1 - 1e-4) / (1 - np.clip(p_lgbm, 1e-4, 1 - 1e-4)))
    rows = []
    for name, X in (("LendingClub sub-grade only", lc[:, None]), ("My LightGBM only", logit_p[:, None]),
                    ("Both together", np.c_[lc, logit_p])):
        oof = cross_val_predict(LogisticRegression(), (X - X.mean(0)) / X.std(0), y, cv=5, method="predict_proba")[:, 1]
        rows.append({"inputs": name, "cv_auc": roc_auc_score(y, oof)})
    pd.DataFrame(rows).to_csv(config.RESULTS_DIR / "incremental_information.csv", index=False)


def explain(lgbm, logit, X_test: pd.DataFrame) -> pd.DataFrame:
    import shap

    imp, values, Xs = model.shap_importance(lgbm, X_test)
    direction = []
    for j, col in enumerate(Xs.columns):
        if col in features.NUMERIC_FEATURES and np.nanstd(values[:, j]) > 0:
            r = pd.Series(Xs[col].to_numpy()).corr(pd.Series(values[:, j]))
            direction.append("higher value -> more risk" if r > 0 else "higher value -> less risk")
        else:
            direction.append("category")
    imp["direction"] = imp["feature"].map(dict(zip(Xs.columns, direction)))
    imp.to_csv(config.RESULTS_DIR / "shap_importance.csv", index=False)
    model.logistic_coefficients(logit).to_csv(config.RESULTS_DIR / "logistic_coefficients.csv", index=False)

    fig, ax = plt.subplots(figsize=(7, 5))
    top = imp.head(12)[::-1]
    ax.barh(top["feature"], top["mean_abs_shap"], color=BLUE)
    ax.set_title("What moves a borrower's risk most (mean |SHAP|, LightGBM)")
    save(fig, "05_shap_importance")

    shap.summary_plot(values, Xs, show=False, max_display=12)
    plt.gcf().set_size_inches(8, 5.5)
    plt.title("How each factor pushes risk up (right) or down (left)")
    save(plt.gcf(), "06_shap_beeswarm")
    return imp


def fair_rates(test: pd.DataFrame, p_lgbm, lgd: float) -> pd.DataFrame:
    """Week 8: price every loan by its own risk, then see who is charged too much or too little."""
    t = test.assign(model_pd=p_lgbm)
    t["fair_rate"] = finance.fair_rate(t["model_pd"], t["term_months"], lgd)
    t["gap"] = t["int_rate"] / 100 - t["fair_rate"]
    t["fico_band"] = pd.cut(t["fico_mid"], [0, 680, 700, 720, 740, 760, 900], right=False,
                            labels=["<680", "680-699", "700-719", "720-739", "740-759", "760+"])
    t["income_band"] = pd.qcut(t["annual_inc"], 4, labels=["Q1 (lowest)", "Q2", "Q3", "Q4 (highest)"])
    t["dti_band"] = pd.cut(t["dti"].clip(0, 60), [-1, 10, 20, 30, 60], labels=["0-10", "10-20", "20-30", "30+"])
    t["sub_grade_group"] = t["sub_grade"].str[0]
    rows = []
    for seg in ["grade", "purpose", "fico_band", "income_band", "dti_band", "home_ownership"]:
        for value, g in t.groupby(seg, observed=True):
            if len(g) < 500:
                continue
            rows.append(
                {"segment": seg, "value": str(value), "loans": len(g),
                 "mean_interest_rate": g["int_rate"].mean() / 100, "mean_fair_rate": g["fair_rate"].mean(),
                 "mean_gap": g["gap"].mean(),
                 # ex-post: shift the rate by how far lenders' real return landed from the hurdle (risk-free + margin)
                 "fair_rate_from_realised_return": float(g["int_rate"].mean() / 100 - (finance.pool_irr(g) - config.RISK_FREE_RATE - config.REQUIRED_MARGIN)), "mean_model_pd": g["model_pd"].mean(),
                 # the same formula fed with the group's ACTUAL default rate (a reality check on the model)
                 "fair_rate_from_actual_defaults": float(finance.fair_rate(g["defaulted"].mean(), g["term_months"], lgd).mean()),
                 "actual_default_rate": g["defaulted"].mean(), "realised_annual_return": finance.pool_irr(g)}
            )
    out = pd.DataFrame(rows)
    out.to_csv(config.RESULTS_DIR / "fair_rate_gaps.csv", index=False)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    g = out[out["segment"] == "grade"]
    x = np.arange(len(g))
    ax.bar(x - 0.27, g["mean_interest_rate"], 0.27, color=BLUE, label="LendingClub rate")
    ax.bar(x, g["mean_fair_rate"], 0.27, color=GREEN, label="Fair rate (my model's risk)")
    ax.bar(x + 0.27, g["fair_rate_from_realised_return"], 0.27, color=RED, label="Fair rate (from lenders' real return)")
    ax.set_xticks(x, g["value"])
    ax.set_title("Charged rate vs fair rate by grade")
    ax.legend(frameon=False)
    pct(ax)
    save(fig, "07_fair_rate_by_grade")

    # sub-grade level: where is the pricing furthest from the risk?
    sg = t.groupby("sub_grade").agg(loans=("gap", "size"), gap=("gap", "mean"), rate=("int_rate", "mean"),
                                    default=("defaulted", "mean"), model_pd=("model_pd", "mean")).reset_index()
    sg.to_csv(config.RESULTS_DIR / "fair_rate_gap_by_subgrade.csv", index=False)
    return out


def invest(train: pd.DataFrame, test: pd.DataFrame, p_lgbm) -> pd.DataFrame:
    """Week 9: ways of picking loans, judged on 2014-15 outcomes the models never saw."""
    ret_model = model.load_return_model()
    pred = ret_model.predict(model.return_features(test))
    s = finance.compare_strategies(test, p_lgbm, share=0.2, n_boot=200, pred_return=pred)
    s.to_csv(config.RESULTS_DIR / "investment_strategies.csv", index=False)

    # How selective should an investor be? Sweep the share on a held-out year AND on the test years.
    fit = train[train["issue_year"] <= config.VALID_YEAR - 1]
    val = train[(train["issue_year"] == config.VALID_YEAR) & (train["term_months"] == 36)]
    mv, _ = model.train_return_model(fit, valid_year=config.VALID_YEAR - 1)
    pv = pd.Series(mv.predict(model.return_features(val)), index=val.index)
    pt = pd.Series(pred, index=test.index)
    rows = []
    for share in (0.05, 0.1, 0.2, 0.3, 0.5, 1.0):
        rows.append({"share_of_loans_funded": share,
                     "validation_2013_return": finance.pool_irr(val[pv.rank(pct=True) > 1 - share]),
                     "test_2014_15_return": finance.pool_irr(test[pt.rank(pct=True) > 1 - share]),
                     "test_loans": int((pt.rank(pct=True) > 1 - share).sum())})
    pd.DataFrame(rows).to_csv(config.RESULTS_DIR / "investment_share_sweep.csv", index=False)

    fig, ax = plt.subplots(figsize=(9, 4.4))
    err = [s["annual_return"] - s["ci95_low"], s["ci95_high"] - s["annual_return"]]
    colors = [GREY] * (len(s) - 1) + [GREEN]
    ax.barh(s["strategy"][::-1], s["annual_return"][::-1], xerr=[e[::-1] for e in err], color=colors[::-1], capsize=3)
    ax.axvline(config.RISK_FREE_RATE, color=GREY, ls=":")
    ax.set_title("Yearly return of each strategy, 2014-15 loans (95% range from resampling)")
    pct(ax, "x")
    save(fig, "08_investment_strategies")
    return s


def approvals() -> None:
    """Week 9: approved vs rejected applications."""
    cube = pd.read_parquet(config.APP_DATA_DIR / "approval_cube.parquet")
    prof = pd.read_parquet(config.RESULTS_DIR / "approval_profile.parquet")
    early = cube[cube["year"].between(2008, 2013)]
    by_year = rejected.approval_rate(cube, "year")
    by_risk = rejected.approval_rate(early, "risk_bin")
    by_dti = rejected.approval_rate(early, "dti_bin")
    by_amt = rejected.approval_rate(early, "amount_bin")
    by_emp = rejected.approval_rate(prof[prof["year"].between(2008, 2013)], "emp_bin")
    by_state = rejected.approval_rate(early, "state").sort_values("approval_rate")
    for name, t in (("year", by_year), ("risk_bin", by_risk), ("dti_bin", by_dti), ("amount_bin", by_amt),
                    ("emp_bin", by_emp), ("state", by_state)):
        t.to_csv(config.RESULTS_DIR / f"approval_by_{name}.csv", index=False)

    risk_order = ["<600", "600-639", "640-659", "660-679", "680-699", "700-719", "720-749", "750+"]
    dti_order = ["invalid (<0)", "0-10", "10-20", "20-30", "30-40", "40+"]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))
    for ax, t, order, title in (
        (axes[0], by_risk, risk_order, "by risk score (2008-13)"),
        (axes[1], by_dti, dti_order, "by debt-to-income % (2008-13)"),
        (axes[2], by_year.assign(year=lambda d: d["year"].astype(str)), sorted(by_year["year"].astype(str)), "by year"),
    ):
        key = "year" if "year" in t.columns else t.columns[0]
        tt = t.set_index(key).reindex(order)
        ax.bar(tt.index, tt["approval_rate"], color=BLUE)
        ax.set_title(f"Share of applications approved {title}", fontsize=10)
        ax.tick_params(axis="x", rotation=45, labelsize=8)
        pct(ax)
    save(fig, "09_approval_rates")


# ---------------------------------------------------------------------------------
def main() -> None:
    config.RESULTS_DIR.mkdir(exist_ok=True)
    df = data.load_clean()
    train, test = data.split_train_test(df)
    logit, lgbm, meta = model.load_models()
    X_test = features.build_features(test)
    p_lgbm, p_logit = model.predict_pd(lgbm, X_test), model.predict_pd(logit, X_test)
    lgd = meta["lgd"]

    print("EDA ...")
    eda(df)
    print("grade economics ...")
    grade_view(test, lgd)
    print("model vs LendingClub ...")
    compare_with_lc(test, p_logit, p_lgbm)
    print("SHAP ...")
    explain(lgbm, logit, X_test)
    print("fair rates ...")
    fair_rates(test, p_lgbm, lgd)
    print("investment strategies ...")
    invest(train, test, p_lgbm)
    print("approvals ...")
    approvals()

    summary = {
        "n_clean_loans": len(df), "n_train": len(train), "n_test": len(test), "lgd": lgd,
        "overall_default_rate": float(df["defaulted"].mean()), "test_default_rate": float(test["defaulted"].mean()),
    }
    (config.RESULTS_DIR / "summary.json").write_text(json.dumps(summary, indent=2))
    print("done; see results/ and results/figures/")


if __name__ == "__main__":
    main()
