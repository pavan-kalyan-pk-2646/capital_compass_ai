from backend.risk_engine import calculate_risk_score

score = calculate_risk_score(
    age=25,
    income=50000,
    years=10,
    loss=7
)

print("Risk Score:", score)