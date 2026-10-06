
import os
import requests
from dotenv import load_dotenv

load_dotenv()

url = "https://api.paystack.co/transaction/initialize"

headers = {
    "Authorization": f"Bearer {os.getenv('PAYSTACK_SECRET_KEY')}",
    "Content-Type": "application/json"
}

payload = {
    "email": "testcustomer@example.com",
    "amount": 500000,
    "currency": "NGN"
}

response = requests.post(
    url,
    headers=headers,
    json=payload,
    timeout=30
)

response.raise_for_status()
result = response.json()

if result.get("status"):
    print("Payment initialized!")
    print("Payment URL:", result["data"]["authorization_url"])
    print("Reference:", result["data"]["reference"])
else:
    print(result.get("message"))