import requests

try:
    r = requests.get("http://127.0.0.1:11434/api/tags", timeout=10)

    print("Status:", r.status_code)
    print(r.text)

except Exception as e:
    print("ERROR:", e)