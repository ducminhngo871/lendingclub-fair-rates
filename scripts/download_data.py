"""Step 0: download the LendingClub data from Kaggle into data/raw/ (about 650 MB, free).

You need a free Kaggle account and an API token (Kaggle -> Settings -> API -> Create New Token).
Put the token in the KAGGLE_API_TOKEN environment variable, or save it as ~/.kaggle/access_token
(or use the older ~/.kaggle/kaggle.json). Never commit the token to GitHub.
"""

import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from lc_rates import config  # noqa: E402


def main() -> None:
    if config.ACCEPTED_RAW.exists() and config.REJECTED_RAW.exists():
        print("Data already downloaded:", config.RAW_DIR)
        return

    token_file = Path.home() / ".kaggle" / "access_token"
    if "KAGGLE_API_TOKEN" not in os.environ and token_file.exists():
        os.environ["KAGGLE_API_TOKEN"] = token_file.read_text().strip()

    exe = shutil.which("kaggle") or str(Path(sys.executable).parent / "kaggle")
    config.RAW_DIR.mkdir(parents=True, exist_ok=True)
    subprocess.run([exe, "datasets", "download", "-d", config.KAGGLE_DATASET, "-p", str(config.RAW_DIR)], check=True)

    archive = config.RAW_DIR / "lending-club.zip"
    with zipfile.ZipFile(archive) as z:  # the zip holds each file twice; keep only the compressed copies
        for name in z.namelist():
            if name.endswith(".csv.gz"):
                z.extract(name, config.RAW_DIR)
    archive.unlink()
    print("Done:", *(p.name for p in config.RAW_DIR.glob("*.csv.gz")))


if __name__ == "__main__":
    main()
