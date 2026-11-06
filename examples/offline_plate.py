"""Create and reread a 100 x 60 mm DXF plate without AutoCAD.
This example does not convert DXF to DWG. Output goes to output/ by default.
"""
import argparse
from pathlib import Path
import ezdxf

def create_plate(destination):
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    doc = ezdxf.new("R2010")
    doc.units = ezdxf.units.MM
    for name, color in [("PLATE", 7), ("HOLES", 2), ("DIM", 1)]:
        doc.layers.new(name, dxfattribs={"color": color})
    model = doc.modelspace()
    model.add_lwpolyline([(0, 0), (100, 0), (100, 60), (0, 60)], close=True, dxfattribs={"layer": "PLATE"})
    for x, y in [(10, 10), (90, 10), (90, 50), (10, 50)]:
        model.add_circle((x, y), 3, dxfattribs={"layer": "HOLES"})
    dim = model.add_linear_dim(base=(0, -12), p1=(0, 0), p2=(100, 0), dxfattribs={"layer": "DIM"}, override={"dimtxt": 3, "dimasz": 2.5})
    dim.render()
    doc.saveas(destination)
    saved = ezdxf.readfile(destination)
    entities = saved.modelspace()
    if saved.audit().has_errors:
        raise RuntimeError("DXF audit failed")
    outline = list(entities.query('LWPOLYLINE[layer=="PLATE"]'))
    circles = list(entities.query('CIRCLE[layer=="HOLES"]'))
    dimensions = list(entities.query("DIMENSION"))
    if len(outline) != 1 or not outline[0].closed or len(circles) != 4 or len(dimensions) != 1:
        raise RuntimeError("Plate structure verification failed")
    points = list(outline[0].get_points("xy"))
    if points != [(0, 0), (100, 0), (100, 60), (0, 60)] or any(abs(c.dxf.radius - 3) > 1e-9 for c in circles):
        raise RuntimeError("Plate geometry verification failed")
    if saved.units != ezdxf.units.MM:
        raise RuntimeError("Drawing units verification failed")
    print(f"Verified 100 x 60 mm plate, 4 holes diameter 6 mm, 1 native dimension: {destination}")
    return saved

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "output/offline-plate.dxf")
    create_plate(parser.parse_args().output)
