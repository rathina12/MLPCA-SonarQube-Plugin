#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python -m unittest discover -s tests -v
python -m compileall -q analyzer
python analyzer/run.py examples --output .mlpca/issues.json
python - <<'PY'
import json
p=json.load(open('.mlpca/issues.json'))
assert p['mlpca']['parseFailures']==[], p['mlpca']['parseFailures']
assert any(x['ruleId']=='ML003' for x in p['issues']), p['issues']
print('end-to-end report validation: OK')
PY
