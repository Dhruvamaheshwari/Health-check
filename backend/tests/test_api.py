import pytest
from fastapi.testclient import TestClient

import main


@pytest.fixture(scope="module")
def client():
    with TestClient(main.app) as c:
        yield c


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok", "model_ready": True}


def test_meta_and_cohort(client):
    meta = client.get("/api/meta").json()
    assert len(meta["features"]) == 7 and meta["auc"] > 0.6
    cohort = client.get("/api/cohort").json()
    assert len(cohort) == 120
    risks = [p["risk"] for p in cohort]
    assert risks == sorted(risks, reverse=True)


def test_predict_matches_cohort_and_responds_to_change(client):
    p = client.get("/api/cohort").json()[0]
    same = client.post("/api/predict", json={"features": p["features"]}).json()
    assert same["risk"] == pytest.approx(p["risk"])
    lower = {**p["features"], "prior_admissions": 0, "ed_visits": 0}
    assert client.post("/api/predict", json={"features": lower}).json()["risk"] < p["risk"]


def test_predict_validation_and_clamping(client):
    assert client.post("/api/predict", json={"features": {"age": 50}}).status_code == 422
    p = client.get("/api/cohort").json()[0]["features"]
    r = client.post("/api/predict", json={"features": {**p, "age": 999}})
    assert r.status_code == 200 and 0 <= r.json()["risk"] <= 1
