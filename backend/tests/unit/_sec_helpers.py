# -*- coding: utf-8 -*-
import io as _io
import os as _os

# 从 backend/tests/unit 上溯 4 级到仓库根
_REPO = _os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))))


def _read(rel):
    return _io.open(_os.path.join(_REPO, rel), encoding="utf-8", errors="replace").read()
