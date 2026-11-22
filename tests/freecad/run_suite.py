"""Run native test suite from FreeCADCmd (not system Python).

Writes machine-readable report; shell wrapper checks it fail-closed.
"""
import json
import os
from pathlib import Path
import sys
import unittest

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
import FreeCAD as App  # MUST use native FreeCAD Python runtime
import Part
import Sketcher

outdir = Path(os.environ.get('SUN_GEAR_TEST_DIR', str(root/'build'/'freecad-test')))
outdir.mkdir(parents=True, exist_ok=True)
suite = unittest.defaultTestLoader.discover(str(root/'tests'/'freecad'), pattern='test_*.py')
with (outdir/'unittest.log').open('w', encoding='utf-8') as log:
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
status = 'PASS' if result.wasSuccessful() and result.testsRun >= 13 else 'FAIL'
report = {
    'runtime': 'REAL_FREECAD',
    'freecad_version': list(App.Version()),
    'status': status,
    'tests_run': result.testsRun,
    'failures': [{'test':str(t),'trace':msg} for t,msg in result.failures],
    'errors': [{'test':str(t),'trace':msg} for t,msg in result.errors],
    'skipped': [{'test':str(t),'reason':reason} for t,reason in result.skipped],
    'generated_models': {},
    'generated_drives': {},
}
if status == 'PASS':
    # Rebuild after the tests in a clean document, then retain the genuine
    # editable .FCStd and FreeCAD-generated STEP files as CI artifacts.
    try:
        from cad.freecad_adapter import export_adapter
        for style in ('square', 'star'):
            native, step = export_adapter(style, outdir/'models')
            for artifact in (native, step):
                if Path(artifact).stat().st_size < 1000:
                    raise RuntimeError('FreeCAD export is missing or empty: ' + artifact)
            report['generated_models'][style] = {
                'fcstd': str(Path(native).relative_to(outdir)),
                'step': str(Path(step).relative_to(outdir))}
        from cad.freecad_drive import export_drive
        from cad.drive_geometry import STUDIES
        for study in STUDIES:
            for style in ('square','star'):
                native, step = export_drive(study, style, outdir/'drives')
                for artifact in (native, step):
                    if Path(artifact).stat().st_size < 1000:
                        raise RuntimeError('FreeCAD drive export missing or empty: '+artifact)
                report['generated_drives'][study+'_'+style] = {
                    'fcstd': str(Path(native).relative_to(outdir)),
                    'step': str(Path(step).relative_to(outdir)),
                    'status': 'PITCH_REFERENCE_ONLY'}
    except Exception:
        import traceback
        report['errors'].append({'test':'native_model_export', 'trace':traceback.format_exc()})
        status = 'FAIL'
        report['status'] = status
(outdir/'result.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print('NATIVE FREECAD TESTS:', status, result.testsRun)
if status != 'PASS':
    raise SystemExit(1)
