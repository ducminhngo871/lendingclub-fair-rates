"""Step 5: squash the 27.6M rejected applications (and all accepted ones) into small count tables."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lc_rates import config, rejected  # noqa: E402

if __name__ == "__main__":
    main, profile = rejected.build_cubes()
    config.APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    main.to_parquet(config.APP_DATA_DIR / "approval_cube.parquet", index=False)
    profile.to_parquet(config.RESULTS_DIR / "approval_profile.parquet", index=False)
    total = main[["n_accepted", "n_rejected"]].sum()
    print(f"main cube: {len(main):,} rows | profile cube: {len(profile):,} rows")
    print(f"accepted {total.n_accepted:,}  rejected {total.n_rejected:,}  approval rate {total.n_accepted / total.sum():.2%}")
