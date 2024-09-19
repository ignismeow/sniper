import csv
import asyncio
from web3 import Web3
import json

# Define WebSocket connection to Ethereum node (Infura)
LOCAL_WSS = 'wss://mainnet.infura.io/ws/v3/bb7f5d16efc7438b846edc2f49a972d6'
provider = Web3(Web3.LegacyWebSocketProvider(LOCAL_WSS))
print("WebSocket Provider connected:", provider.is_connected())

# Load the contract ABI and addresses
with open("blockchain_v3.json") as f:
    blockchain = json.load(f)

factory_contract = provider.eth.contract(
    address=blockchain['factoryAddress'],
    abi=blockchain['factoryAbi']
)

SNIPE_LIST_FILE = 'snipeList.csv'

# Function to fetch pools created in the last 1000 blocks
def fetch_recent_pools():
    print("Fetching pools from the last 1000 blocks...")

    # Get the current block number
    current_block = provider.eth.block_number
    from_block = current_block - 1000 if current_block > 1000 else 0

    # Create a filter to capture PoolCreated events from the last 1000 blocks
    event_filter = factory_contract.events.PoolCreated.create_filter(from_block=from_block, to_block='latest')

    # Open CSV file to write pool data
    with open(SNIPE_LIST_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Pair Address', 'Token 0', 'Token 1', 'Fee', 'Tick Spacing'])

        # Iterate through each event
        for event in event_filter.get_all_entries():
            token0, token1, fee, tickSpacing, pair_address = event.args.token0, event.args.token1, event.args.fee, event.args.tickSpacing, event.args.pool
            print(f"New pair detected: {pair_address}, token0: {token0}, token1: {token1}, fee: {fee}, tickSpacing: {tickSpacing}")

            # Only consider pools with WETH
            if token0 != blockchain['WETHAddress'] and token1 != blockchain['WETHAddress']:
                continue

            # Determine which token is WETH (token0 or token1)
            t0 = token0 if token0 == blockchain['WETHAddress'] else token1
            t1 = token1 if token0 != blockchain['WETHAddress'] else token1

            # Write the pool details to the CSV file
            writer.writerow([pair_address, token0, token1, fee, tickSpacing])

    print(f"Pool data written to {SNIPE_LIST_FILE}")

# Call the function to fetch recent pools
fetch_recent_pools()
