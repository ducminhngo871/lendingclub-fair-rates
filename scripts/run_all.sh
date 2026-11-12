#!/usr/bin/env bash
# Run the whole pipeline, start to finish. Takes about 15 minutes.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python}"

$PY scripts/download_data.py     # 0. get the data from Kaggle
$PY scripts/prepare_data.py      # 1. clean it
$PY scripts/train.py             # 2. train the scoring machines
$PY scripts/build_rejected.py    # 3. approved-vs-rejected tables
$PY scripts/analyze.py           # 4. every table and figure for the report
$PY scripts/build_app_data.py    # 5. files the web app reads
$PY -m pytest -q                 # 6. checks
echo "All done. Start the app with:  streamlit run app/streamlit_app.py"
