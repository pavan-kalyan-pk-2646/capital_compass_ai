def compute_allocation(risk_score):

    if risk_score > 75:
        return {"Stocks": 80, "Bonds": 15, "Cash": 5}
    elif risk_score > 45:
        return {"Stocks": 55, "Bonds": 30, "Cash": 15}
    else:
        return {"Stocks": 30, "Bonds": 45, "Cash": 25}
def stress_test(amount):

    return {
        "Crash (-30%)": round(amount * 0.7, 2),
        "Bear (-15%)": round(amount * 0.85, 2),
        "Bull (+20%)": round(amount * 1.2, 2)
    }