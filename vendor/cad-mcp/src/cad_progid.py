"""Discover installed AutoCAD COM registrations without starting CAD.

Daihua integration addition, MIT. Explicit override wins; otherwise prefer
newer registered versions and retain the generic ProgID as a fallback.
"""
import os
import re

_PATTERN = re.compile(r"AutoCAD\.Application(?:\.\d+(?:\.\d+)*)?", re.I)


def autocad_progids(names=None, override=None):
    override = override if override is not None else os.environ.get("DAIHUA_CAD_PROGID")
    if override:
        return [override]
    if names is None:
        names = []
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "") as key:
                i = 0
                while True:
                    try:
                        names.append(winreg.EnumKey(key, i))
                        i += 1
                    except OSError:
                        break
        except (ImportError, OSError):
            pass
    matches = {n for n in names if _PATTERN.fullmatch(n)}
    versions = sorted((n for n in matches if n.lower() != "autocad.application"),
                      key=lambda n: tuple(map(int, n.split(".")[2:])), reverse=True)
    return versions + ["AutoCAD.Application"]
