from fastapi.testclient import TestClient

from app.main import app
from app.data import store


client = TestClient(app)


# ---------------------------------------------------------
# Helper functions
# ---------------------------------------------------------

def check(name, condition, details=""):
    if condition:
        print(f"PASS  {name}")
        if details:
            print(f"      {details}")
        return True
    else:
        print(f"FAIL  {name}")
        if details:
            print(f"      {details}")
        return False


def show_title(text):
    print()
    print("=" * 60)
    print(text)
    print("=" * 60)


# ---------------------------------------------------------
# Start with clean data
# ---------------------------------------------------------

store.reset()

show_title("TALUS - ZONE B ESCALATION DEMO")


# ---------------------------------------------------------
# 1. INITIAL STATE
# ---------------------------------------------------------

print()
print("1. INITIAL STATE")

r = client.get("/api/zones")

if r.status_code != 200:
    print("FAIL  Could not get zones")
    print(r.text)
    raise SystemExit(1)

zones = {z["zone_id"]: z for z in r.json()["zones"]}

check(
    "Initial zones",
    (
        zones["A"]["risk_score"] == 22
        and zones["B"]["risk_score"] == 48
        and zones["C"]["risk_score"] == 35
        and zones["D"]["risk_score"] == 28
    ),
    f"A={zones['A']['risk_score']} "
    f"B={zones['B']['risk_score']} "
    f"C={zones['C']['risk_score']} "
    f"D={zones['D']['risk_score']}"
)


# ---------------------------------------------------------
# Base Zone B features
# ---------------------------------------------------------

BASE_FEATURES = {
    "rainfall_24h_mm": 35.0,
    "rainfall_7d_mm": 140.0,
    "slope_angle_deg": 58.0,
    "slope_height_m": 45.0,
    "rock_type": "sandstone",
    "crack_density": 0.42,
    "crack_severity": "moderate",
    "blast_frequency_per_week": 2.0,
    "blast_vibration_ppv_mms": 9.5,
    "days_since_inspection": 12,
    "prior_incident": 0,
    "groundwater_proxy": 0.35,
}


# ---------------------------------------------------------
# 2. EVENT 1 - RAIN
# ---------------------------------------------------------

print()
print("2. EVENT 1 - RAIN INCREASE")

EVENT1 = {
    **BASE_FEATURES,
    "rainfall_24h_mm": 55.0,
    "rainfall_7d_mm": 210.0,
    "groundwater_proxy": 0.45,
}

r = client.post(
    "/api/risk/predict",
    json={
        "zone_id": "B",
        "features": EVENT1,
    },
)

if r.status_code != 200:
    print("FAIL  Event 1 request failed")
    print(r.text)
    raise SystemExit(1)

event1_score = r.json()["risk_score"]

check(
    "Event 1 risk",
    58 <= event1_score <= 63,
    f"B risk = {event1_score}"
)


# ---------------------------------------------------------
# 3. EVENT 2 - CRACKS + BLASTING
# ---------------------------------------------------------

print()
print("3. EVENT 2 - CRACKS + BLASTING")

EVENT2 = {
    **EVENT1,
    "crack_density": 0.6,
    "crack_severity": "severe",
    "blast_frequency_per_week": 3.0,
    "blast_vibration_ppv_mms": 12.0,
    "days_since_inspection": 15,
    "groundwater_proxy": 0.5,
}

r = client.post(
    "/api/risk/predict",
    json={
        "zone_id": "B",
        "features": EVENT2,
    },
)

if r.status_code != 200:
    print("FAIL  Event 2 request failed")
    print(r.text)
    raise SystemExit(1)

event2_score = r.json()["risk_score"]

check(
    "Event 2 risk",
    68 <= event2_score <= 74,
    f"B risk = {event2_score}"
)


# ---------------------------------------------------------
# 4. TREND
# ---------------------------------------------------------

print()
print("4. TREND")

r = client.get("/api/zones/B/trend")

if r.status_code != 200:
    print("FAIL  Trend request failed")
    print(r.text)
    raise SystemExit(1)

trend = r.json()

check(
    "Rapid increase",
    trend["rapid_increase"] is True,
    f"rapid_increase = {trend['rapid_increase']}"
)


# ---------------------------------------------------------
# 5. WHAT-IF
# ---------------------------------------------------------

print()
print("5. WHAT-IF - RAINFALL = 80mm")

r = client.post(
    "/api/simulation/what-if",
    json={
        "zone_id": "B",
        "overrides": {
            "rainfall_24h_mm": 80.0
        },
    },
)

if r.status_code != 200:
    print("FAIL  What-if request failed")
    print(r.text)
    raise SystemExit(1)

what_if = r.json()

simulated_score = what_if["simulated"]["risk_score"]
simulated_band = what_if["simulated"]["risk_band"]

check(
    "What-if becomes Critical",
    simulated_score >= 80 and simulated_band == "Critical",
    f"B risk = {simulated_score}, band = {simulated_band}"
)


# ---------------------------------------------------------
# 6. SAFE ROUTE
# ---------------------------------------------------------

print()
print("6. SAFE ROUTE")

route_body = {
    "start": {
        "zone_id": "A",
        "lat": 20.51,
        "lng": 80.115,
    },
    "end": {
        "zone_id": "D",
        "lat": 20.58,
        "lng": 80.165,
    },
}

r = client.post(
    "/api/routes/safe",
    json=route_body,
)

if r.status_code != 200:
    print("FAIL  Route request failed")
    print(r.text)
    raise SystemExit(1)

route = r.json()

check(
    "Route avoids Zone B",
    route["avoided_zones"] == ["B"],
    f"avoided_zones = {route['avoided_zones']}"
)


# ---------------------------------------------------------
# FINAL RESULT
# ---------------------------------------------------------

print()
print("=" * 60)
print("DEMO COMPLETE")
print("=" * 60)

print()
print(f"Initial B risk : 48")
print(f"Event 1 B risk : {event1_score}")
print(f"Event 2 B risk : {event2_score}")
print(f"Trend          : {trend['rapid_increase']}")
print(f"What-if risk   : {simulated_score}")
print(f"What-if band   : {simulated_band}")
print(f"Avoided zones  : {route['avoided_zones']}")

print()
print("If every check above says PASS, the Zone B demo is working.")
print()