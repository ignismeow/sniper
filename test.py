from web3 import Web3
import json


# Connect Ethereum network

LOCAL_HTTP = 'ws://127.0.0.1:8545'
web3 = Web3(Web3.LegacyWebSocketProvider(LOCAL_HTTP))

# Connect acccount
private_key = '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80'
account =  web3.eth.account.from_key(private_key)

# import abi's and addresses
with open('blockchain.json') as f:
    blockchain = json.load(f)

erc20_abi = blockchain['erc20Abi']
erc20_bytecode = blockchain['erc20Bytecode']
factory_address = blockchain['factoryAddress']
factory_abi = blockchain['factoryAbi']
router_address = blockchain['routerAddress']
router_abi = blockchain['routerAbi']
weth_address = blockchain['WETHAddress']

erc20_contract = web3.eth.contract(abi=erc20_abi, bytecode=erc20_bytecode)
factory_contract = web3.eth.contract(address=factory_address, abi=factory_abi)
router_contract = web3.eth.contract(address=router_address, abi=router_abi)


# Deploy ERC20 Token
def deploy_erc20_token():   
    nonce = web3.eth.get_transaction_count(account.address)
    transaction = erc20_contract.constructor(
        "ABC Token",
        "ABC",
        web3.to_wei("1000000000", 'ether')
    ).build_transaction({
        'chainId': 31337,  # Update to your network's chain ID
        'gas': 5000000,
        'gasPrice': web3.to_wei('20', 'gwei'),
        'nonce': nonce
    })

    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    
    token_address = tx_receipt.contractAddress
    print(f"Test token deployed: {token_address}")
    return token_address
  
def create_liquidity_pool(token_address):
    try:
        nonce = web3.eth.get_transaction_count(account.address)
        transaction = factory_contract.functions.createPair(
            weth_address,
            token_address
        ).build_transaction({
            'chainId': 31337,  # Update to your network's chain ID
            'gas': 5000000,
            'gasPrice': web3.to_wei('20', 'gwei'),
            'nonce': nonce
        })

        signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        web3.eth.wait_for_transaction_receipt(tx_hash)
        print('Test liquidity pool deployed')
    except Exception as e:
        print(f"Error creating liquidity pool: {e}")
        raise


def approve_token_for_router(token_address):
    try:
        token_contract = web3.eth.contract(address=token_address, abi=erc20_abi)
        nonce = web3.eth.get_transaction_count(account.address)
        transaction = token_contract.functions.approve(
            router_address,
            web3.to_wei("10000", 'ether')
        ).build_transaction({
            'chainId': 31337,  # Update to your network's chain ID
            'gas': 500000,
            'gasPrice': web3.to_wei('20', 'gwei'),
            'nonce': nonce
        })

        signed_txn = web3.eth.account.sign_transaction(transaction, private_key=private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        web3.eth.wait_for_transaction_receipt(tx_hash)
        print('Token approved for router')
    except Exception as e:
        print(f"Error approving token for router: {e}")
        raise

def add_liquidity(token_address):
    try:
        nonce = web3.eth.get_transaction_count(account.address)
        transaction = router_contract.functions.addLiquidityETH(
            token_address,
            web3.to_wei("1000", 'ether'),
            0,  # Minimum ABC tokens to add
            0,  # Minimum ETH to add
            account.address,
            int(web3.eth.get_block('latest')['timestamp']) + 600,  # Deadline (10 minutes from now)
        ).build_transaction({
            'chainId': 31337,  # Update to your network's chain ID
            'value': web3.to_wei("10", 'ether'),  # Add 10 ETH
            'gas': 5000000,
            'gasPrice': web3.to_wei('20', 'gwei'),
            'nonce': nonce
        })

        signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
        web3.eth.wait_for_transaction_receipt(tx_hash)
        print('Liquidity added to the pool')
    except Exception as e:
        print(f"Error adding liquidity: {e}")
        raise


def main():
    try:
        token_address = deploy_erc20_token()
        create_liquidity_pool(token_address)
        approve_token_for_router(token_address)
        add_liquidity(token_address)
    except Exception as e:
        print("Error during deployment or liquidity addition: ", e) 
  
if __name__ == "__main__":
    main()
