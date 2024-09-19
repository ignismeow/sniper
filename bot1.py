import asyncio
import json
import csv
import time
from web3 import Web3

LOCAL_WSS = 'ws://127.0.0.1:8545'
provider = Web3(Web3.LegacyWebSocketProvider(LOCAL_WSS))

private_key = '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80'
account =  provider.eth.account.from_key(private_key)
wallet_address = account.address
print(wallet_address)

# Load contract ABIs and addresses
with open("blockchain.json") as f:
    blockchain = json.load(f)

factory_contract = provider.eth.contract(
    address=blockchain['factoryAddress'],
    abi=blockchain['factoryAbi']
)

router_contract = provider.eth.contract(
    address=blockchain['routerAddress'],
    abi=blockchain['routerAbi']
)

SNIPE_LIST_FILE = 'snipeList.csv'
TOKEN_LIST_FILE = 'tokenList.csv'

# Function to initialize PairCreated event listener
def init():
    print("Event listener started")
    event_filter = factory_contract.events.PairCreated.create_filter(from_block='latest')
    
    while True:
        print("Checking for new events...")
        for event in event_filter.get_all_entries():
            token0, token1, pair_address = event.args.token0, event.args.token1, event.args.pair
            print(f"New pair detected: {pair_address}, token0: {token0}, token1: {token1}")

            if token0 != blockchain['WETHAddress'] and token1 != blockchain['WETHAddress']:
                continue

            t0 = token0 if token0 == blockchain['WETHAddress'] else token1
            t1 = token1 if token0 != blockchain['WETHAddress'] else token1

            with open(SNIPE_LIST_FILE, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([pair_address, t0, t1])

        # Use asyncio.sleep for non-blocking delay
        asyncio.run(asyncio.sleep(1))

# Function to handle sniping
async def snipe():
    print('Snipe loop')
    with open(SNIPE_LIST_FILE, 'r') as f:
        reader = csv.reader(f)
        snipe_list = list(reader)

    if not snipe_list:
        return

    for snipe in snipe_list:
        pair_address, weth_address, token_address = snipe
        print(f"Trying to snipe {token_address} on {pair_address}")

        pair_contract = provider.eth.contract(
            address=pair_address,
            abi=blockchain['pairAbi']
        )
        total_supply = pair_contract.functions.totalSupply().call()
        if total_supply == 0:
            print(f"Pair {pair_address} is empty, skipping...")
            continue

        token_in = weth_address
        token_out = token_address

        amount_in = Web3.to_wei(0.1, 'ether')
        amounts_out = router_contract.functions.getAmountsOut(amount_in, [token_in, token_out]).call()

        amount_out_min = amounts_out[1] - (amounts_out[1] * 5 // 100)
        print(f"Buying new token: tokenIn: {amount_in} {token_in} (WETH), tokenOut: {amount_out_min} {token_out}")

        try:
            tx = router_contract.functions.swapTokensForExactTokens(
                amount_in,
                amount_out_min,
                [token_in, token_out],
                blockchain['recipient'],
                int(time.time()) + 1000 * 60 * 10
            ).build_transaction({
                'from': wallet_address,
                'gas': 5000000,
                'gasPrice': provider.to_wei('20', 'gwei'),
                'nonce': provider.eth.get_transaction_count(wallet_address)
            })
            signed_tx = provider.eth.account.sign_transaction(tx, account.key)
            tx_hash = provider.eth.send_raw_transaction(signed_tx.raw_transaction)
            receipt = provider.eth.wait_for_transaction_receipt(tx_hash)
            print(f"Transaction confirmed in block: {receipt.blockNumber}")
        except Exception as e:
            print(f"Transaction failed: {e}")

        # Update snipeList after transaction
        snipe_list = [item for item in snipe_list if item != snipe]
        with open(SNIPE_LIST_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(snipe_list)

# Function to manage positions
async def manage_position():
    print("Managing positions...")
    with open(TOKEN_LIST_FILE, 'r') as f:
        reader = csv.reader(f)
        token_list = list(reader)

    for token in token_list:
        block_number, weth_address, token_address, price = token
        print(f"Checking position for token {token_address} bought at price {price}")

        token_contract = provider.eth.contract(
            address=token_address,
            abi=blockchain['abi']
        )
        balance = token_contract.functions.balanceOf(blockchain['recipient']).call()
        print(f"Current balance of {token_address}: {balance}")

        stop_loss_threshold = Web3.to_wei(0.01, 'ether')
        take_profit_threshold = Web3.to_wei(0.2, 'ether')

        if balance > stop_loss_threshold:
            print(f"Selling {token_address} due to stop loss")
            # Add stop loss logic here
        elif balance > take_profit_threshold:
            print(f"Selling {token_address} to take profit")
            # Add take profit logic here

# Main function to run the bot
async def main():
    print("Trading bot starting...")
    loop = asyncio.get_event_loop()

    # Initialize PairCreated listener in a separate thread
    loop.run_in_executor(None, init)


    while True:
        print('Heartbeat')
        await snipe()
        await manage_position()
        await asyncio.sleep(3)

if __name__ == "__main__":
    asyncio.run(main())

