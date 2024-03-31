import requests


r = requests.get("http://127.0.0.1:8000/checkdb")


# first define json then post
body = {"name": "Invent SEXY", "description": "agi"}
r = requests.post("http://127.0.0.1:8000/projects/", json=body)

print(r.status_code)
print(r.text)
