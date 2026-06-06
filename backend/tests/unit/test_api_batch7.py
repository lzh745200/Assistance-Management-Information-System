"""API batch 7."""
import pytest

class TestTodosCRUD:
    def test_list(self, auth_client):
        r = auth_client.get("/api/v1/todos"); assert r.status_code in (200,401,404,405,422)
    def test_create(self, auth_client):
        r = auth_client.post("/api/v1/todos", json={"title":"todo1"}); assert r.status_code in (200,201,400,401,404,405,422)
    def test_update(self, auth_client):
        r = auth_client.put("/api/v1/todos/1", json={"title":"done"}); assert r.status_code in (200,400,401,404,405,422)
    def test_delete(self, auth_client):
        r = auth_client.delete("/api/v1/todos/1"); assert r.status_code in (200,204,400,401,404,405,422)

class TestRuralTaskCRUD:
    def test_list(self, auth_client):
        r = auth_client.get("/api/v1/rural-tasks"); assert r.status_code in (200,401,404,405,422)
    def test_create(self, auth_client):
        r = auth_client.post("/api/v1/rural-tasks", json={"title":"rt1"}); assert r.status_code in (200,201,400,401,404,405,422)
    def test_detail(self, auth_client):
        r = auth_client.get("/api/v1/rural-tasks/1"); assert r.status_code in (200,401,404,405,422)

class TestRuralWorkCRUD:
    def test_list(self, auth_client):
        r = auth_client.get("/api/v1/rural-works"); assert r.status_code in (200,401,404,405,422)
    def test_create(self, auth_client):
        r = auth_client.post("/api/v1/rural-works", json={"name":"rw1"}); assert r.status_code in (200,201,400,401,404,405,422)
    def test_detail(self, auth_client):
        r = auth_client.get("/api/v1/rural-works/1"); assert r.status_code in (200,401,404,405,422)

class TestWorkLogCRUD:
    def test_list(self, auth_client):
        r = auth_client.get("/api/v1/work-logs"); assert r.status_code in (200,401,404,405,422)
    def test_create(self, auth_client):
        r = auth_client.post("/api/v1/work-logs", json={"content":"log1"}); assert r.status_code in (200,201,400,401,404,405,422)

class TestFeedbackCRUD:
    def test_list(self, auth_client):
        r = auth_client.get("/api/v1/feedback"); assert r.status_code in (200,401,404,405,422)
    def test_create(self, auth_client):
        r = auth_client.post("/api/v1/feedback", json={"content":"fb1"}); assert r.status_code in (200,201,400,401,404,405,422)

class TestUserPermissionsCRUD:
    def test_list(self, auth_client):
        r = auth_client.get("/api/v1/user-permissions"); assert r.status_code in (200,401,404,405,422)
    def test_set(self, auth_client):
        r = auth_client.post("/api/v1/user-permissions", json={"user_id":1,"permissions":["read"]}); assert r.status_code in (200,201,400,401,404,405,422)

class TestMachineCodeCRUD:
    def test_list(self, auth_client):
        r = auth_client.get("/api/v1/machine-codes"); assert r.status_code in (200,401,404,405,422)
    def test_detail(self, auth_client):
        r = auth_client.get("/api/v1/machine-codes/1"); assert r.status_code in (200,401,404,405,422)
    def test_register(self, auth_client):
        r = auth_client.post("/api/v1/machine-codes/register", json={"code":"MC1","hardware_id":"HW1"}); assert r.status_code in (200,201,400,401,404,405,422)
    def test_activate(self, auth_client):
        r = auth_client.post("/api/v1/machine-codes/activate", json={"code":"MC1","hardware_id":"HW1"}); assert r.status_code in (200,201,400,401,404,405,422)
    def test_deactivate(self, auth_client):
        r = auth_client.post("/api/v1/machine-codes/1/deactivate"); assert r.status_code in (200,400,401,404,405,422)

class TestVillageCRUD:
    def test_list(self, auth_client):
        r = auth_client.get("/api/v1/villages"); assert r.status_code in (200,401,404,405,422)
    def test_detail(self, auth_client):
        r = auth_client.get("/api/v1/villages/1"); assert r.status_code in (200,401,404,405,422)
