# -*- coding: utf-8 -*-
"""cache_service.EntityCacheManager 同步包装覆盖率测试"""

from unittest.mock import MagicMock, patch

import sys

mod = sys.modules.get("app.services.cache_service")
if mod is None:
    import importlib

    mod = importlib.import_module("app.services.cache_service")


def _svc():
    svc = mod.EntityCacheManager("village", ttl=60)
    svc._cache = MagicMock()
    return svc


def test_get_hit_records_metric():
    svc = _svc()
    svc._cache._b.get.return_value = {"id": 1}
    with patch.object(mod, "metrics") as m:
        assert svc.get("list") == {"id": 1}
        m.record_hit.assert_called_once()
        m.record_miss.assert_not_called()
    svc._cache._b.get.assert_called_once_with("village:list")


def test_get_miss_records_metric():
    svc = _svc()
    svc._cache._b.get.return_value = None
    with patch.object(mod, "metrics") as m:
        assert svc.get("stats") is None
        m.record_miss.assert_called_once()


def test_set_uses_default_ttl():
    svc = _svc()
    svc._cache._b.set.return_value = True
    assert svc.set("list", [1, 2]) is True
    svc._cache._b.set.assert_called_once_with("village:list", [1, 2], ttl=60)


def test_set_explicit_ttl():
    svc = _svc()
    svc.set("detail", {"x": 1}, ttl=5)
    svc._cache._b.set.assert_called_once_with("village:detail", {"x": 1}, ttl=5)


def test_invalidate():
    svc = _svc()
    svc._cache._b.delete.return_value = True
    assert svc.invalidate("list") is True
    svc._cache._b.delete.assert_called_once_with("village:list")


def test_invalidate_all_deletes_three_keys():
    svc = _svc()
    svc.invalidate_all()
    deleted = [c.args[0] for c in svc._cache._b.delete.call_args_list]
    assert deleted == ["village:list", "village:stats", "village:detail"]


def test_default_ttl_used_when_none():
    svc = mod.EntityCacheManager("fund")
    assert svc.ttl == mod.EntityCacheManager.DEFAULT_TTL
