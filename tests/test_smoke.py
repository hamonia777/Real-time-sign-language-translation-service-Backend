"""배포 전 기본 동작 확인용 스모크 테스트.

DB/Redis 에 연결하지 않도록 TestClient 를 lifespan 없이 생성한다.
(lifespan 은 SQLModel.metadata.create_all 을 실행하므로 CI 에서는 실행하지 않는다.)
"""

from fastapi.testclient import TestClient

from main.main import app


client = TestClient(app)


def test_home_page_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_static_page_served():
    response = client.get("/login.html")
    assert response.status_code == 200


def test_static_assets_mounted():
    assert client.get("/css/home.css").status_code == 200
    assert client.get("/logo.png").status_code == 200


def test_openapi_schema_generated():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "paths" in response.json()
