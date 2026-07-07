import requests

url = "https://script.google.com/macros/s/AKfycbwSZRq3zqLHaWMJEqbQhR0L7w1eG8_oEc7YE2MOKMr7M1tqtHtIRnVWs0TIolTNAYgE0g/exec"
payload = {
    "to": "a.revanth2006@gmail.com",
    "otp": "888888"
}
try:
    response = requests.post(url, json=payload, allow_redirects=True)
    print("Status Code:", response.status_code)
    print("Response Text:", response.text)
except Exception as e:
    print("Exception:", e)
