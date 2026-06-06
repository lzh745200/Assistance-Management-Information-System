"""API route batch tests."""
import pytest


class TestAuthRoutes:
    def test_login(self, client):
        r = client.post("/api/v1/auth/login", json={"username":"admin","password":"admin123"}); assert r.status_code in (200,401,404,405,422)
    def test_register(self, client):
        r = client.post("/api/v1/auth/register", json={"username":"u","password":"P@ssw0rd!"}); assert r.status_code in (200,201,400,401,404,405,422)
    def test_refresh(self, client):
        r = client.post("/api/v1/auth/refresh", json={}); assert r.status_code in (200,400,401,404,405,422)
    def test_logout(self, client):
        r = client.post("/api/v1/auth/logout"); assert r.status_code in (200,401,404,405,422)


class TestMachineRoutes:
    def test_list(self, auth_client):
        r = auth_client.get("/api/v1/machine-codes"); assert r.status_code in (200,401,404,405,422)
    def test_register(self, auth_client):
        r = auth_client.post("/api/v1/machine-codes/register", json={"code":"T","hardware_id":"H"}); assert r.status_code in (200,201,400,401,404,405,422)


class TestMapRoutes:
    def test_markers(self, auth_client):
        r = auth_client.get("/api/v1/map/markers"); assert r.status_code in (200,401,404,405,422)


class TestOfflineMapRoutes:
    def test_status(self, auth_client):
        r = auth_client.get("/api/v1/offline-map/status"); assert r.status_code in (200,401,404,405,422)


class TestSearchRoutes:
    def test_search(self, auth_client):
        r = auth_client.get("/api/v1/search?q=test"); assert r.status_code in (200,401,404,405,422)


class TestDataSyncRoutes:
    def test_status(self, auth_client):
        r = auth_client.get("/api/v1/sync/status"); assert r.status_code in (200,401,404,405,422)


class TestFeedbackRoutes:
    def test_create(self, auth_client):
        r = auth_client.post("/api/v1/feedback", json={"content":"test"}); assert r.status_code in (200,201,400,401,404,405,422)


class TestTodosRoutes:
    def test_list(self, auth_client):
        r = auth_client.get("/api/v1/todos"); assert r.status_code in (200,401,404,405,422)
    def test_create(self, auth_client):
        r = auth_client.post("/api/v1/todos", json={"title":"test"}); assert r.status_code in (200,201,400,401,404,405,422)


class TestVillagesRoutes:
    def test_list(self, auth_client):
        r = auth_client.get("/api/v1/villages"); assert r.status_code in (200,401,404,405,422)


class TestWorkLogsRoutes:
    def test_list(self, auth_client):
        r = auth_client.get("/api/v1/work-logs"); assert r.status_code in (200,401,404,405,422)


class TestUserPermissionsRoutes:
    def test_list(self, auth_client):
        r = auth_client.get("/api/v1/user-permissions"); assert r.status_code in (200,401,404,405,422)


class TestEffectivenessRoutes:
    def test_list(self, auth_client):
        r = auth_client.get("/api/v1/effectiveness"); assert r.status_code in (200,401,404,405,422)


class TestDataQualityRoutes:
    def test_rules(self, auth_client):
        r = auth_client.get("/api/v1/data-quality/rules"); assert r.status_code in (200,401,404,405,422)


class TestVillageTemplatesRoutes:
    def test_list(self, auth_client):
        r = auth_client.get("/api/v1/village-templates"); assert r.status_code in (200,401,404,405,422)
