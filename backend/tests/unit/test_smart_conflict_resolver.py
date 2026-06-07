"""智能冲突解决器单元测试"""
import pytest

def test_service_exists():
    from app.services.smart_conflict_resolver import SmartConflictResolver
    assert SmartConflictResolver is not None
