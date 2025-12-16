from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  # read from .env file
  api_key=os.getenv("OPENROUTER_API_KEY"),
)

# First API call with reasoning
response = client.chat.completions.create(
  model="nvidia/nemotron-3-nano-30b-a3b:free",
  messages=[
          {
            "role": "user",
            "content": "Explain the computer networks briefly."
          }
        ],
  extra_body={"reasoning": {"enabled": True}}
)

# Extract the assistant message with reasoning_details
response = response.choices[0].message
print(response.content)