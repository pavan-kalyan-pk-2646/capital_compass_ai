from langchain_ollama import ChatOllama

# timeout=120  — stops the request hanging if Ollama is slow/unresponsive
# num_predict=512 — caps token output so explanation/compliance don't run forever
llm = ChatOllama(model="phi3:mini", timeout=120, num_predict=512)

def generate_response(prompt):
    response = llm.invoke(prompt)
    return response.content