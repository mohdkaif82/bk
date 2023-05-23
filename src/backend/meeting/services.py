import jwt
import time
import requests


def generate_jwt(key, secret):
    header = {"alg": "HS256", "typ": "JWT"}

    payload = {"iss": key, "exp": int(time.time() + 3600)}

    token = jwt.encode(payload, secret, algorithm="HS256", headers=header)
    return token.decode("utf-8")


def get_request(url, api_key, api_secret):
    token = generate_jwt(api_key, api_secret)
    headers = {
        'content-type': "application/json",
        'Content-Type': "application/json",
        'cache-control': "no-cache",
        'Authorization': "Bearer " + token
    }
    response = requests.request("GET", url, headers=headers)
    return response


def post_request(url, api_key, api_secret, data):
    token = generate_jwt(api_key, api_secret)
    headers = {
        'content-type': "application/json",
        'Content-Type': "application/json",
        'cache-control': "no-cache",
        'Authorization': "Bearer " + token
    }
    response = requests.request("POST", url, headers=headers, data=data)
    return response


def delete_request(url, api_key, api_secret):
    token = generate_jwt(api_key, api_secret)
    headers = {
        'content-type': "application/json",
        'Content-Type': "application/json",
        'cache-control': "no-cache",
        'Authorization': "Bearer " + token
    }
    response = requests.request("DELETE", url, headers=headers)
    return response
