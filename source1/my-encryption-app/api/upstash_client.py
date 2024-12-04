"""
This file is used to interact with the Upstash Redis instance. It contains functions to set and get values from the Redis instance.
The functions make use of the requests library to send HTTP requests to the Upstash Redis instance.

Note: The functions in this file are used by the main application to interact with the Redis instance.

"""

import os
import requests

UPSTASH_REDIS_URL = os.getenv("UPSTASH_REDIS_URL")  # Set this as the REST URL from Upstash
UPSTASH_REDIS_TOKEN = os.getenv("UPSTASH_REDIS_PASSWORD")  # Set this as the password/token from Upstash

# Headers for the HTTP requests to the Upstash Redis instance (includes the authorization token)
headers = {
    "Authorization": f"Bearer {UPSTASH_REDIS_TOKEN}"
}

# Functions to interact with the Upstash Redis instance
def redis_set(key, value, ttl=None):
    payload = {
        "command": "SET",
        "args": [key, value]
    }
    if ttl:
        payload["ttl"] = ttl
    response = requests.post(UPSTASH_REDIS_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

# Function to get a value from the Redis instance
def redis_get(key):
    payload = {
        "command": "GET",
        "args": [key]
    }
    response = requests.post(UPSTASH_REDIS_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

# Function to set multiple key-value pairs in the Redis instance
def redis_hset(key, mapping):
    payload = {
        "command": "HSET",
        "args": [key] + [item for pair in mapping.items() for item in pair]
    }
    response = requests.post(UPSTASH_REDIS_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

# Function to get all fields and values of a hash stored in the Redis instance
def redis_hgetall(key):
    payload = {
        "command": "HGETALL",
        "args": [key]
    }
    response = requests.post(UPSTASH_REDIS_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()

# Function to set the expiration time for a key in the Redis instance
def redis_expire(key, ttl):
    payload = {
        "command": "EXPIRE",
        "args": [key, ttl]
    }
    response = requests.post(UPSTASH_REDIS_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()
