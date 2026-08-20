import os
from langchain_openai import ChatOpenAI

# Uses OpenAI's hosted API instead of a local Ollama server, since Vercel's
# serverless functions have no way to run/host an Ollama model.
# Set OPENAI_API_KEY in your Vercel project's Environment Variables.
llm = ChatOpenAI(
    model="gpt-4o-mini",
    timeout=120,
    max_tokens=512,
    api_key=os.environ.get("OPENAI_API_KEY"),
)

def generate_response(prompt):
    response = llm.invoke(prompt)
    return response.content