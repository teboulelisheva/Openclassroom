from fastapi.testclient import TestClient
from project5.api import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_predict():
    response = client.post(
        "/predict",
        json={"feature1": 0, "feature2": 1}
    )
    assert response.status_code == 200
    assert "prediction" in response.json()
