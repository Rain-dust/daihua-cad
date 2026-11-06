"""Audit native-CAD DXF readbacks for editable, semantically layered delivery.

Run against DXF exported from the saved DWG, not only the generator's DXF.
Dependencies: ezdxf. --manifest adds project-specific required layers/types.
"""
import argparse
import collections
import json
from pathlib import Path

import ezdxf

REFERENCES = {'IMAGE', 'PDFUNDERLAY', 'DWFUNDERLAY', 'DGNUNDERLAY', 'OLE2FRAME', 'ACAD_PROXY_ENTITY'}


def audit(path, spec=None, allow_references=False):
    spec = spec or {}
    doc = ezdxf.readfile(path)
    model = doc.modelspace()
    errors, warnings = [], []
    counts = collections.Counter(e.dxftype() for e in model)
    layer_counts = collections.Counter(e.dxf.layer for e in model)
    if not len(model):
        errors.append('Empty modelspace')
    if layer_counts.get('0', 0) or layer_counts.get('Defpoints', 0):
        errors.append('Top-level model geometry on 0 or Defpoints')
    if len(model) == 1 and counts.get('INSERT'):
        (errors if spec.get('reject_whole_drawing_block') else warnings).append(
            'Entire model is a single block: verify this matches the requested editable deliverable')
    foreign = collections.Counter(e.dxftype() for e in doc.entitydb.values()
                                  if e.is_alive and e.dxftype() in REFERENCES)
    if foreign and not allow_references:
        errors.append('Raster/underlay/OLE/proxy content: ' + str(dict(foreign)))
    overrides = []
    missing_layers = []
    for e in model:
        if e.dxf.layer not in doc.layers:
            missing_layers.append(e.dxf.handle)
        if (e.dxf.get('color', 256) != 256 or e.dxf.hasattr('true_color')
                or e.dxf.get('linetype', 'BYLAYER').upper() != 'BYLAYER'
                or e.dxf.get('lineweight', -1) != -1):
            overrides.append(e.dxf.handle)
    if overrides:
        errors.append(f'{len(overrides)} top-level entities override ByLayer appearance')
    if missing_layers:
        errors.append(f'{len(missing_layers)} entities reference undefined layers')
    for layer, minimum in spec.get('required_layers', {}).items():
        if layer_counts.get(layer, 0) < minimum:
            errors.append(f'Required occupied model layer missing: {layer}')
    for kind, minimum in spec.get('required_types', {}).items():
        if counts.get(kind, 0) < minimum:
            errors.append(f'Required native entity type missing: {kind}')
    for layer, allowed in spec.get('layer_types', {}).items():
        bad = [e.dxf.handle for e in model if e.dxf.layer == layer and e.dxftype() not in allowed]
        if bad:
            errors.append(f'{layer} has wrong entity types: {len(bad)}')
    hatch_count = 0
    associative = 0
    for hatch in model.query('HATCH'):
        hatch_count += 1
        if not hatch.dxf.associative:
            if spec.get('require_associative_hatches'):
                errors.append(f'Hatch {hatch.dxf.handle} is not associative')
            continue
        associative += 1
        for edge_path in hatch.paths:
            handles = edge_path.source_boundary_objects
            if not handles or any(h not in doc.entitydb or not doc.entitydb[h].is_alive for h in handles):
                errors.append(f'Hatch {hatch.dxf.handle} has unresolved associated boundary')
    if spec.get('open_in_modelspace') and doc.header.get('$TILEMODE') != 1:
        errors.append('Saved DWG does not default to modelspace')
    viewports = []
    for layout in doc.layouts:
        if layout.name == 'Model':
            continue
        for vp in layout.query('VIEWPORT'):
            if vp.dxf.id <= 1:
                continue
            denominator = vp.dxf.view_height / vp.dxf.height
            locked = bool(vp.dxf.flags & 16384)
            viewports.append({'layout': layout.name, 'scale_denominator': denominator, 'locked': locked})
            expected_scale = spec.get('viewport_scale')
            if expected_scale and (abs(denominator - expected_scale) > 1e-6 or not locked):
                errors.append(f'Viewport {layout.name} has wrong/unlocked scale')
    if spec.get('viewport_scale') and not viewports:
        errors.append('Missing drawing layout viewport')
    inventory = []
    for name in sorted(layer_counts):
        layer = doc.layers.get(name)
        inventory.append({'name': name, 'description': layer.description,
                          'model_entities': layer_counts[name],
                          'types': dict(collections.Counter(e.dxftype() for e in model if e.dxf.layer == name)),
                          'color_aci': layer.dxf.color, 'lineweight': layer.dxf.lineweight,
                          'plottable': bool(layer.dxf.plot),
                          'on': not layer.is_off(), 'frozen': layer.is_frozen(), 'locked': layer.is_locked()})
    return {'file': str(Path(path).resolve()), 'passed': not errors, 'errors': errors,
            'warnings': warnings, 'model_count': len(model), 'types': dict(counts),
            'layers': inventory, 'top_level_overrides': overrides,
            'foreign_content': dict(foreign), 'hatches': hatch_count,
            'associative_hatches': associative, 'tilemode': doc.header.get('$TILEMODE'),
            'viewports': viewports}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('files', nargs='+', type=Path)
    parser.add_argument('--manifest', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--allow-references', action='store_true',
                        help='Use only for explicitly authorized reference content')
    args = parser.parse_args()
    specs = json.loads(args.manifest.read_text('utf-8')) if args.manifest else {}
    results = [audit(f, specs.get(f.stem, {}), args.allow_references) for f in args.files]
    report = {'passed': all(r['passed'] for r in results), 'drawings': len(results), 'results': results}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'passed': report['passed'], 'drawings': len(results),
                      'failures': [{'file': r['file'], 'errors': r['errors']} for r in results if not r['passed']]}))
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
