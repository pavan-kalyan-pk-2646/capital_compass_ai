def calculate_risk_score(age, income, years, loss):

    age_score = max(0, 100 - age)
    income_score = min(100, income / 1000)
    horizon_score = min(100, years * 5)
    tolerance_score = loss * 10

    risk_score = (
        age_score * 0.2 +
        income_score * 0.2 +
        horizon_score * 0.3 +
        tolerance_score * 0.3
    )

    return int(min(100, risk_score))