#!/usr/bin/env python
"""Verify project_milestones import after data isolation fix."""
import os
os.environ["ENVIRONMENT"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key-for-ci"

try:
    from app.api.v1.project_milestones import router
    print(f"IMPORT_OK: {len(router.routes)} routes")
    
    # Also verify filter_by_data_scope is imported
    import app.api.v1.project_milestones as pm
    assert hasattr(pm, 'filter_by_data_scope'), "filter_by_data_scope not imported!"
    print("filter_by_data_scope: imported OK")
    
    # Verify HTTPException is available (used in change-logs)
    from fastapi import HTTPException
    print("HTTPException: available")
    
    print("ALL_CHECKS_PASSED")
except Exception as e:
    print(f"FAIL: {e}")
    import traceback
    traceback.print_exc()
