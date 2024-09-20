import csv
import asyncio
from web3 import Web3
import json
from web3.exceptions import TimeExhausted

# Define WebSocket connection to Ethereum node (Infura)
LOCAL_WSS = 'https://sepolia.infura.io/v3/bb7f5d16efc7438b846edc2f49a972d6'
provider = Web3(Web3.HTTPProvider(LOCAL_WSS))
print("WebSocket Provider connected:", provider.is_connected())

# Convert addresses to checksum format
def to_checksum(address):
    return Web3.to_checksum_address(address)

# Load the contract ABI and addresses
with open("blockchain_v3.json") as f:
    blockchain = json.load(f)

factory_contract = provider.eth.contract(
    address=to_checksum(blockchain['factoryAddress']),
    abi=blockchain['factoryAbi']
)

router_contract = provider.eth.contract(
    address=to_checksum(blockchain['routerAddress']),  # Uniswap V3 Router Address
    abi=blockchain['routerAbi']
)

# Wallet address and private key
wallet_address = to_checksum("0x83037d8F3Daa4a29c0024B9e5F9F8b3dBC6794b5")
private_key = "4ff9407108178f487bbd54d33a2eecc12aa1bef343ba275046c431940cd4abfb"

SNIPE_LIST_FILE = 'snipeList.csv'
TOKEN_LIST_FILE = 'tokenList.csv'  # New file for successful swaps

# Function to fetch the latest nonce
def get_nonce(wallet_address):
    return provider.eth.get_transaction_count(wallet_address, 'pending')

# Function to perform the token swap
def swap_weth_to_token(pair_address, token0, token1, amount_in_wei, nonce):
    # Check if token0 is WETH or token1 is WETH
    weth_address = to_checksum(blockchain['WETHAddress'])
    pair_address = to_checksum(pair_address)
    token0 = to_checksum(token0)
    token1 = to_checksum(token1)
    
    target_token = token0 if token1 == weth_address else token1
    
    # Approve the Uniswap Router to spend WETH from your wallet
    weth_contract = provider.eth.contract(address=weth_address, abi=blockchain['ERC20Abi'])
    approve_txn = weth_contract.functions.approve(
        blockchain['routerAddress'],
        amount_in_wei
    ).build_transaction({
        'from': wallet_address,
        'nonce': nonce,  # Fetch latest nonce
        'gas': 200000,
        'gasPrice': provider.to_wei('30', 'gwei')
    })
    
    # Sign and send the approve transaction
    signed_approve_txn = provider.eth.account.sign_transaction(approve_txn, private_key)
    approve_txn_hash = provider.eth.send_raw_transaction(signed_approve_txn.raw_transaction)
    print("Approve transaction sent with hash:", approve_txn_hash.hex())
    
    # Wait for approval to be mined
    provider.eth.wait_for_transaction_receipt(approve_txn_hash)

    new_gas_price = provider.to_wei('45', 'gwei')  # Set a higher gas price than the original one

    # Perform the swap using Uniswap's Router contract
    swap_txn = router_contract.functions.exactInputSingle({
        'tokenIn': weth_address,               # WETH address
        'tokenOut': target_token,              # The token you're swapping to
        'fee': 3000,                          # Default fee tier (e.g., 0.3%)
        'recipient': wallet_address,           # Your wallet address
        'deadline': int(provider.eth.get_block('latest')['timestamp']) + 60 * 10,  # 10 minutes from now
        'amountIn': amount_in_wei,             # Amount of WETH being swapped (in wei)
        'amountOutMinimum': 0,                 # Minimum amount of the target token (adjust for slippage)
        'sqrtPriceLimitX96': 0                 # Set price limit to 0 (no limit)
    }).build_transaction({
        'from': wallet_address,
        'nonce': nonce + 1,  # Increment nonce for the new transaction
        'gas': 300000,
        'gasPrice': new_gas_price              # Increased gas price
    })

    # Sign and send the swap transaction
    signed_swap_txn = provider.eth.account.sign_transaction(swap_txn, private_key)
    swap_txn_hash = provider.eth.send_raw_transaction(signed_swap_txn.raw_transaction)
    print("Swap transaction sent with hash:", swap_txn_hash.hex())

    # Initialize receipt variable
    receipt = None

    # Wait for the transaction to be mined
    try:
        receipt = provider.eth.wait_for_transaction_receipt(swap_txn_hash, timeout=300)
    except TimeExhausted:
        print("Transaction timed out.")

    # Check if the receipt was successfully obtained
    if receipt is not None:
        print("Swap transaction mined in block:", receipt.blockNumber)
        log_successful_swap(token0, token1, amount_in_wei)
    else:
        print("No receipt available. The transaction may have failed or timed out.")

# Function to log successful swaps to a CSV file
def log_successful_swap(token0, token1, amount_in_wei):
    amount_in_eth = provider.from_wei(amount_in_wei, 'ether')
    with open(TOKEN_LIST_FILE, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([token0, token1, amount_in_eth])  # Log token addresses and swapped amount
        print(f"Logged successful swap: {amount_in_eth} of {token0} for {token1}")

# Function to swap WETH to the selected token from the CSV
def swap_tokens_from_csv():
    amount_in_eth = 0.009  # Amount of WETH to swap (in ETH)
    amount_in_wei = provider.to_wei(amount_in_eth, 'ether')

    with open(SNIPE_LIST_FILE, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            pair_address = row['Pair Address']
            token0 = row['Token 0']
            token1 = row['Token 1']
            nonce = get_nonce(wallet_address)
            print(f"Swapping WETH for token in pair: {pair_address}")
            swap_weth_to_token(pair_address, token0, token1, amount_in_wei, nonce)

# Call the function to swap tokens from the CSV
swap_tokens_from_csv()
