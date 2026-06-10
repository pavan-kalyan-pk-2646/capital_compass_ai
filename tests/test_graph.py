from backend.graph import build_graph

graph = build_graph()

profile = {
    "age": 22,
    "income": 100000,
    "years": 20,
    "loss": 9,
    "amount": 50000
}

initial_state = {
    "profile": profile,
    "logs": []
}

result = graph.invoke(initial_state)

print("\nFINAL RESULT:\n")
print("Risk Score:", result["risk_score"])
print("Allocation:", result["allocation"])
print("Stress Test:", result["stress_test"])
print("\nExplanation:\n", result["explanation"])

print("\nAgent Logs:")
for log in result["logs"]:
    print("-", log)