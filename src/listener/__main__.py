from chainlistener.listener import Listener
from yaml_env.parser import parse_config
import asyncio

config = parse_config("config.yaml")

mainnet_listener = Listener(
    config["web3_urls"]["mainnet_url"],
    config["web3_keys"]["infura_key"],
    config["contracts"]["mainnet_bridge"],
    config["contracts"]["mainnet_usdc_token"],
    _bridge_abi="MainChainBridge.json",
)

sidechain_listener = Listener(
    config["web3_urls"]["polygon_url"],
    config["web3_keys"]["alchemy_key"],
    config["contracts"]["polygon_bridge"],
    config["contracts"]["polygon_usdc_bridged_token"],
    _bridge_abi="SideChainBridge.json",
)


async def execute_transaction(data):
    if data["result"] == True:
        if data["chain_id"] == 800001:
            print("initialized from mainnet - creating tx on side chain")
            if data["event"] == "BridgedTokens":
                print(f'event: {data["event"]}')
                data["bridged_token_address"] = data["token_address"]
                data["token_address"] = config["contracts"][
                    "polygon_usdc_bridged_token"
                ]
                data["chain_id"] = 5
                tx = sidechain_listener.execute_transaction(data)
                print(tx)
            elif data["event"] == "ReturnedTokens":
                print(f'event: {data["event"]}')

        elif data["chain_id"] == 5:
            print("initialized from side chain - tx on mainnet")
            if data["event"] == "BridgedTokens":
                print(f'event: {data["event"]}')
                print(data)
            elif data["event"] == "ReturnedTokens":
                # create transaction on mainnet for return
                print(f'event: {data["event"]}')
                data["bridged_token_address"] = data["token_address"]
                data["token_address"] = config["contracts"]["mainnet_usdc_token"]
                data["chain_id"] = 800001
                tx = mainnet_listener.execute_transaction(data)
                print(tx)
        return True

    return False


async def loop_mainnet_BridgedTokens(event_filter, poll_interval):
    while True:
        for BridgedTokens in event_filter.get_new_entries():
            result = mainnet_listener.check_transaction(BridgedTokens)
            await execute_transaction(result)
        await asyncio.sleep(poll_interval)


async def loop_mainnet_ReturnedTokens(event_filter, poll_interval):
    while True:
        for ReturnedTokens in event_filter.get_new_entries():
            result = mainnet_listener.check_transaction(ReturnedTokens)
            await execute_transaction(result)
        await asyncio.sleep(poll_interval)


async def loop_sidechain_BridgedTokens(event_filter, poll_interval):
    while True:
        for BridgedTokens in event_filter.get_new_entries():
            result = sidechain_listener.check_transaction(BridgedTokens)
            await execute_transaction(result)
        await asyncio.sleep(poll_interval)


async def loop_sidechain_ReturnedTokens(event_filter, poll_interval):
    while True:
        for ReturnedTokens in event_filter.get_new_entries():
            result = sidechain_listener.check_transaction(ReturnedTokens)
            await execute_transaction(result)
        await asyncio.sleep(poll_interval)


async def run_tasks():
    event_mainnet_BridgedTokens_filter = (
        mainnet_listener.bridge_contract.events.BridgedTokens.createFilter(
            fromBlock="latest"
        )
    )
    event_mainnet_ReturnedTokens_filter = (
        mainnet_listener.bridge_contract.events.ReturnedTokens.createFilter(
            fromBlock="latest"
        )
    )

    event_sidechain_BridgedTokens_filter = (
        sidechain_listener.bridge_contract.events.BridgedTokens.createFilter(
            fromBlock="latest"
        )
    )
    event_sidechain_ReturnedTokens_filter = (
        sidechain_listener.bridge_contract.events.ReturnedTokens.createFilter(
            fromBlock="latest"
        )
    )

    routines = [
        loop_mainnet_BridgedTokens(
            event_filter=event_mainnet_BridgedTokens_filter, poll_interval=2
        ),
        loop_mainnet_ReturnedTokens(
            event_filter=event_mainnet_ReturnedTokens_filter, poll_interval=2
        ),
        loop_sidechain_BridgedTokens(
            event_filter=event_sidechain_BridgedTokens_filter, poll_interval=2
        ),
        loop_sidechain_ReturnedTokens(
            event_filter=event_sidechain_ReturnedTokens_filter, poll_interval=2
        ),
    ]

    result = await asyncio.gather(*routines, return_exceptions=True)
    return result


def main():
    asyncio.run(run_tasks())


if __name__ == "__main__":
    main()
