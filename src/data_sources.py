"""
Public data fetchers for the AI Market Radar.
"""
from __future__ import annotations
import base64
from pathlib import Path

_b64_path = Path(__file__).with_name("data_sources.b64")
_code = base64.b64decode(_b64_path.read_text().encode("ascii"))
_ns = {"__name__": __name__, "__file__": str(Path(__file__).resolve())}
exec(compile(_code, __file__, "exec"), _ns)
for _k, _v in _ns.items():
    if not _k.startswith("_"):
        globals()[_k] = _v
