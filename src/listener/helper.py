import json


def load_abi(filename):
    with open(f"data/abi/{filename}", "r") as f:
        contract_abi = json.load(f)
    return contract_abi


def check_key(key, dict):
    if key in dict:
        return True
    else:
        return False
