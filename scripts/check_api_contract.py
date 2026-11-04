import os

import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

response = requests.get(f"{BASE_URL}/docs")

print(response.status_code)
print(response.url)