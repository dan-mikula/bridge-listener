from typing import Dict
from yaml_env.parser import parse_config
from web3 import Web3
from web3.middleware import geth_poa_middleware
from helper import check_key, load_abi


class Listener:
    def __init__(
        self,
        _web3_endpoint_url,
        _web3_endpoint_key,
        _bridge_address,
        _token_address,
        _bridge_abi=None,
        _middleware=False,
    ):
        def web3_object():
            web3_object = Web3(Web3.HTTPProvider(self.web3_endpoint_url))
            if _middleware:
                web3_object.middleware_onion.inject(geth_poa_middleware, layer=0)
            return web3_object

        def build_bridge_contract():
            bridge_abi = load_abi(_bridge_abi)
            return self.web3_connection.eth.contract(
                address=self.bridge_address, abi=bridge_abi
            )

        self.config = parse_config("config.yaml")
        self.web3_endpoint_key = _web3_endpoint_key
        self.web3_endpoint_url = f"{_web3_endpoint_url}{self.web3_endpoint_key}"
        self.bridge_address = _bridge_address
        self.token_address = _token_address
        self.web3_connection = web3_object()
        self.gateway_private_key = self.config["gateway"]
        self.gateway_account = self.web3_connection.eth.account.privateKeyToAccount(
            self.gateway_private_key
        )
        self.bridge_contract = build_bridge_contract()

    def check_transaction(self, event_from_contract: Dict):
        result = {}

        # optimize in contract start
        deposit_hash_key_in_contract_emit = check_key(
            "mainDepositHash", event_from_contract["args"]
        )
        if deposit_hash_key_in_contract_emit:
            key_in_emit = "mainDepositHash"
        else:
            key_in_emit = "sideDepositHash"
        # optimize in contract end

        get_tx_receipt = self.get_transaction_receipt(
            event_from_contract["args"][key_in_emit]
        )
        result["result"] = get_tx_receipt["tx_status"]
        # add check if transaction exists
        result["sender"] = event_from_contract["args"]["sender"]
        result["receiver"] = event_from_contract["args"]["receiver"]
        result["token_address"] = self.token_address  # check
        result["deposit_hash"] = event_from_contract["args"][key_in_emit]
        result["amount"] = get_tx_receipt["amount"]
        result["chain_id"] = event_from_contract["args"]["targetChain"]  # check
        result["event"] = event_from_contract["event"]
        return result

    def get_transaction_receipt(self, _depositHash: str) -> Dict:
        result = {}
        transaction_data = self.web3_connection.eth.getTransactionReceipt(_depositHash)
        print(f"transaction receipt: {transaction_data}")
        result["tx_status"] = True
        """
        add error handling
        for now i assume tx is correct. correct erc20 contract used and tx happened.
        get fee from contract. for now: fee is 0.3% and applies
        """
        amount_transferred = transaction_data["logs"][0]["data"]
        amount_bridged = (float.fromhex(amount_transferred) * (100 - 0.3)) / 100
        result["amount"] = int(amount_bridged)
        return result

    def execute_transaction(self, data: Dict):
        nonce = self.web3_connection.eth.getTransactionCount(
            self.gateway_account.address
        )
        if data["event"] == "BridgedTokens":
            build_tx = self.bridge_contract.functions.bridgedTokens(
                data["sender"],
                data["receiver"],
                data["token_address"],
                data["amount"],
                data["deposit_hash"],
                data["chain_id"],
            ).buildTransaction(
                {
                    "gas": 1000000,
                    "gasPrice": Web3.toWei(10, "gwei"),
                    "from": self.gateway_account.address,
                    "nonce": nonce,
                }
            )
        if data["event"] == "ReturnedTokens":
            build_tx = self.bridge_contract.functions.returnedTokens(
                data["sender"],
                data["receiver"],
                data["token_address"],
                data["amount"],
                data["deposit_hash"],
                data["chain_id"],
            ).buildTransaction(
                {
                    "gas": 1000000,
                    "gasPrice": Web3.toWei(10, "gwei"),
                    "from": self.gateway_account.address,
                    "nonce": nonce,
                }
            )
        signed_tx = self.web3_connection.eth.account.signTransaction(
            build_tx, private_key=self.gateway_private_key
        )
        tx = self.web3_connection.eth.sendRawTransaction(signed_tx.rawTransaction)
        return self.web3_connection.toHex(tx)
