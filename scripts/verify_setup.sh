#!/usr/bin/env bash
# Quick check that everything is working
set -e

echo "=== Clinical Trials Analyzer - Health Check ==="

# 1. Python
if [ -d ".venv" ]; then
  PY=".venv/bin/python"
else
  PY="python3"
fi
echo "[OK] Python: $($PY --version)"

# 2. Database connection
$PY - <<'PY'
import sys
try:
    from etl.db import get_connection, count_rows
    conn = get_connection()
    n = count_rows(conn, "trials")
    conn.close()
    print(f"[OK] Database connected - {n} trials in DB")
except Exception as e:
    print(f"[FAIL] Database: {e}")
    print("       Run: make db-up   then   make etl")
    sys.exit(1)
PY

# 3. API smoke test
$PY - <<'PY'
from etl.api_client import fetch_studies_page
data = fetch_studies_page(page_size=1)
assert "studies" in data and len(data["studies"]) >= 1
nct = data["studies"][0]["protocolSection"]["identificationModule"]["nctId"]
print(f"[OK] API reachable - sample trial: {nct}")
PY

echo "=== All checks passed ==="
