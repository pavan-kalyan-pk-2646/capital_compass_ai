import ollama

response = ollama.chat(
    model="phi3:mini",
    messages=[
        {"role": "user", "content": "Explain investment diversification in simple terms."}
    ]
)

print(response["message"]["content"])