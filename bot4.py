from web3 import Web3
import json

# Connect to Ethereum node
infura_url = 'https://sepolia.infura.io/v3/bb7f5d16efc7438b846edc2f49a972d6'
web3 = Web3(Web3.HTTPProvider(infura_url))

# Convert addresses to checksum format
def to_checksum(address):
    return Web3.to_checksum_address(address)

# Uniswap V3 Factory address
factory_address = to_checksum('0x1F98431c8aD98523631AE4a59f267346ea31F984')  # Uniswap V3 Factory Address
factory_abi = json.loads('[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"uint24","name":"fee","type":"uint24"},{"indexed":true,"internalType":"int24","name":"tickSpacing","type":"int24"}],"name":"FeeAmountEnabled","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"oldOwner","type":"address"},{"indexed":true,"internalType":"address","name":"newOwner","type":"address"}],"name":"OwnerChanged","type":"event"},{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"token0","type":"address"},{"indexed":true,"internalType":"address","name":"token1","type":"address"},{"indexed":true,"internalType":"uint24","name":"fee","type":"uint24"},{"indexed":false,"internalType":"int24","name":"tickSpacing","type":"int24"},{"indexed":false,"internalType":"address","name":"pool","type":"address"}],"name":"PoolCreated","type":"event"},{"inputs":[{"internalType":"address","name":"tokenA","type":"address"},{"internalType":"address","name":"tokenB","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"}],"name":"createPool","outputs":[{"internalType":"address","name":"pool","type":"address"}],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"}],"name":"enableFeeAmount","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint24","name":"","type":"uint24"}],"name":"feeAmountTickSpacing","outputs":[{"internalType":"int24","name":"","type":"int24"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"},{"internalType":"address","name":"","type":"address"},{"internalType":"uint24","name":"","type":"uint24"}],"name":"getPool","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"owner","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"parameters","outputs":[{"internalType":"address","name":"factory","type":"address"},{"internalType":"address","name":"token0","type":"address"},{"internalType":"address","name":"token1","type":"address"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"int24","name":"tickSpacing","type":"int24"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"_owner","type":"address"}],"name":"setOwner","outputs":[],"stateMutability":"nonpayable","type":"function"}]')  # Replace with the actual ABI JSON

# Create contract instance
factory_contract = web3.eth.contract(address=factory_address, abi=factory_abi)

# Function to get pool address for token0 and token1
def get_pool_address(token0, token1, fee):
    # Fetch the pool address
    pool_address = factory_contract.functions.getPool(token0, token1, fee).call()
    return pool_address

# Example token addresses (USDC and WETH)
usdc_address = to_checksum('0x4f7a67464b5976d7547c860109e4432d50afb38e')
weth_address = to_checksum('0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9')
fee = 3000  # 0.3% fee tier

# Get pool address
pool_address = get_pool_address(usdc_address, weth_address, fee)
print(f'Pool Address: {pool_address}')
