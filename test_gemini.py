from app.services.gemini import generate_ai_response

response = generate_ai_response(
    "Explain Python in 3 simple sentences."
)

print(response)