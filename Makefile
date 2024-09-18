.PHONY: anvil bot test

# Set environment variables from .env
export $(shell grep -v '^#' .env | xargs)

anvil:
    anvil --fork-url ${MAINNET_RPC_URL_WS}

python = /usr/bin/python3  # Adjust path based on your Python installation location in WSL

bot:
    $(python) bot1.py

test:
    $(python) test.py 