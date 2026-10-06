
import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("PAYSTACK_SECRET_KEY")

if not api_key or not api_key.startswith("sk_test_"):
    raise ValueError("Missing or invalid Paystack test key")

url = "https://api.paystack.co/transaction"

response = requests.get(
    url,
    headers={
        "Authorization": f"Bearer {api_key}"
    },
    params={"perPage": 5, "page": 1},
    timeout=30
)

response.raise_for_status()
data = response.json()

print("API status:", data.get("status"))
print("Message:", data.get("message"))
print("Transactions returned:", len(data.get("data", [])))

for tx in data.get("data", []):
    print({
        "reference": tx.get("reference"),
        "status": tx.get("status"),
        "amount": tx.get("amount"),
        "currency": tx.get("currency")
    })