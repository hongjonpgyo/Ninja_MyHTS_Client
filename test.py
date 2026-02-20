import requests

url = "https://openapi.ls-sec.co.kr:8080/oauth2/token"

data = {
    "grant_type": "client_credentials",
    "appkey": "PSnfXVDGywhF58V74t3QDaZXzgVKshD49Gxj",
    "appsecretkey": "ln5S4NaXcZMXvRur6cU08UrQhHnIbRNG",
    "scope": "oob",
}

res = requests.post(
    url,
    data=data,
    headers={"Content-Type": "application/x-www-form-urlencoded"},
    timeout=10,
)

print(res.status_code)
print(res.text)
