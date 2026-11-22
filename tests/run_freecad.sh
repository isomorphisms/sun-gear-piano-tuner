#!/usr/bin/env bash
# Fail closed: absence of FreeCAD, missing/stale result, skipped or failing tests.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
export SUN_GEAR_TEST_DIR="$ROOT/build/freecad-test"
mkdir -p "$SUN_GEAR_TEST_DIR"
rm -f "$SUN_GEAR_TEST_DIR/result.json" "$SUN_GEAR_TEST_DIR/unittest.log"

if [[ -n "${FREECAD_CMD:-}" ]]; then
  # Command may be a launcher with arguments, e.g. FreeCAD -c; no eval.
  read -r -a command_parts <<< "$FREECAD_CMD"
elif command -v FreeCADCmd >/dev/null; then
  command_parts=(FreeCADCmd)
elif command -v freecadcmd >/dev/null; then
  command_parts=(freecadcmd)
elif command -v freecad >/dev/null; then
  command_parts=(freecad -c)
else
  echo >&2 'FAIL: no real FreeCAD executable found. Set FREECAD_CMD or install FreeCAD.'
  exit 2
fi

status=0
"${command_parts[@]}" "$ROOT/tests/freecad/run_suite.py" || status=$?
if [[ "$status" -ne 0 ]]; then echo >&2 "FreeCAD returned $status"; fi
python3 - "$SUN_GEAR_TEST_DIR/result.json" <<'PY'
import json, pathlib, sys
path = pathlib.Path(sys.argv[1])
if not path.exists():
    sys.exit('FAIL: FreeCAD did not produce an actual native test report')
report = json.loads(path.read_text())
print('FreeCAD', report.get('freecad_version'), report.get('status'), 'tests', report.get('tests_run'))
if (report.get('runtime') != 'REAL_FREECAD' or report.get('status') != 'PASS'
        or report.get('tests_run',0) < 8 or report.get('failures')
        or report.get('errors') or report.get('skipped')):
    sys.exit('FAIL: native FreeCAD tests incomplete or failed')
PY
if [[ "$status" -ne 0 ]]; then exit "$status"; fi
for style in square star; do
  [[ -s "$SUN_GEAR_TEST_DIR/models/sun_gear_adapter_${style}_v1.FCStd" ]] || { echo "FAIL: missing native $style FCStd" >&2; exit 1; }
  [[ -s "$SUN_GEAR_TEST_DIR/models/sun_gear_adapter_${style}_v1.step" ]] || { echo "FAIL: missing native $style STEP" >&2; exit 1; }
done
