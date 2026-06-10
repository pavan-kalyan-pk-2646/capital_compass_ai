from backend.agent import run_agent

profile = {
    "age": 22,
    "income": 100000,
    "years": 20,
    "loss": 9,
    "amount": 50000
}

result = run_agent(profile)

print("Risk Score:", result["risk_score"])
print("Allocation:", result["allocation"])
print("Explanation:\n", result["explanation"])
print("\nAgent Logs:")
print("Stress Test:", result["stress_test"])
for log in result["logs"]:
    print("-", log)