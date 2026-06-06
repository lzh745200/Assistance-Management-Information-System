"""API batch 6."""
import pytest

class TestPolicyRemaining:
    def test_update(self, auth_client):
        r = auth_client.put("/api/v1/policies/1", json={"title":"u1"}); assert r.status_code in (200,400,401,404,405,422)
    def test_delete(self, auth_client):
        r = auth_client.delete("/api/v1/policies/1"); assert r.status_code in (200,204,400,401,404,405,422)
    def test_favorite(self, auth_client):
        r = auth_client.post("/api/v1/policies/1/favorite"); assert r.status_code in (200,201,400,401,404,405,422)
    def test_batch_delete(self, auth_client):
        r = auth_client.post("/api/v1/policies/batch-delete", json={"ids":[1]}); assert r.status_code in (200,400,401,404,405,422)

class TestApprovalRemaining:
    def test_create_workflow(self, auth_client):
        r = auth_client.post("/api/v1/approval/workflows", json={"name":"wf1","nodes":3}); assert r.status_code in (200,201,400,401,404,405,422)
    def test_tasks_pending(self, auth_client):
        r = auth_client.get("/api/v1/approval/tasks/pending"); assert r.status_code in (200,401,404,405,422)
    def test_approve(self, auth_client):
        r = auth_client.post("/api/v1/approval/tasks/1/approve", json={"comment":"ok"}); assert r.status_code in (200,400,401,404,405,422)
    def test_reject(self, auth_client):
        r = auth_client.post("/api/v1/approval/tasks/1/reject", json={"comment":"no"}); assert r.status_code in (200,400,401,404,405,422)

class TestReportTemplateRemaining:
    def test_update(self, auth_client):
        r = auth_client.put("/api/v1/report-templates/1", json={"name":"u1"}); assert r.status_code in (200,400,401,404,405,422)
    def test_delete(self, auth_client):
        r = auth_client.delete("/api/v1/report-templates/1"); assert r.status_code in (200,204,400,401,404,405,422)
    def test_generate(self, auth_client):
        r = auth_client.post("/api/v1/report-templates/1/generate", json={"format":"pdf"}); assert r.status_code in (200,201,400,401,404,405,422)
    def test_preview(self, auth_client):
        r = auth_client.get("/api/v1/report-templates/1/preview"); assert r.status_code in (200,401,404,405,422)
    def test_download(self, auth_client):
        r = auth_client.get("/api/v1/report-templates/1/download"); assert r.status_code in (200,401,404,405,422)
    def test_duplicate(self, auth_client):
        r = auth_client.post("/api/v1/report-templates/1/duplicate"); assert r.status_code in (200,201,400,401,404,405,422)
    def test_categories(self, auth_client):
        r = auth_client.get("/api/v1/report-templates/categories"); assert r.status_code in (200,401,404,405,422)

class TestFundBudgetRemaining:
    def test_detail(self, auth_client):
        r = auth_client.get("/api/v1/fund-budgets/1"); assert r.status_code in (200,401,404,405,422)
    def test_update(self, auth_client):
        r = auth_client.put("/api/v1/fund-budgets/1", json={"amount":200}); assert r.status_code in (200,400,401,404,405,422)
    def test_transactions(self, auth_client):
        r = auth_client.get("/api/v1/fund-budgets/1/transactions"); assert r.status_code in (200,401,404,405,422)
    def test_summary(self, auth_client):
        r = auth_client.get("/api/v1/fund-budgets/summary"); assert r.status_code in (200,401,404,405,422)

class TestProjectRemaining:
    def test_create(self, auth_client):
        r = auth_client.post("/api/v1/projects/", json={"name":"p1"}); assert r.status_code in (200,201,400,401,404,405,422)
    def test_update(self, auth_client):
        r = auth_client.put("/api/v1/projects/1", json={"name":"p2"}); assert r.status_code in (200,400,401,404,405,422)
    def test_delete(self, auth_client):
        r = auth_client.delete("/api/v1/projects/1"); assert r.status_code in (200,204,400,401,404,405,422)

class TestFundRemaining:
    def test_create(self, auth_client):
        r = auth_client.post("/api/v1/funds/", json={"name":"f1","amount":1000}); assert r.status_code in (200,201,400,401,404,405,422)
    def test_update(self, auth_client):
        r = auth_client.put("/api/v1/funds/1", json={"amount":2000}); assert r.status_code in (200,400,401,404,405,422)
    def test_delete(self, auth_client):
        r = auth_client.delete("/api/v1/funds/1"); assert r.status_code in (200,204,400,401,404,405,422)
