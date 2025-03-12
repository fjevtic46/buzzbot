import functions_framework
import os
import requests
import json

import base64
import json
import requests
from solana.rpc.api import Client
from solana.rpc.api import Pubkey
from solana.rpc.api import VersionedTransaction
from solana.rpc.types import TokenAccountOpts
from solana.rpc.types import TxOpts
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed

from solders import keypair
from solders import message
from solders import keypair

@functions_framework.cloud_event
def main(cloud_event):
    data = cloud_event.data
    user_id = os.environ.get("USER_ID")

    print(f"Trigger function 2 for user: {user_id} triggered with data: {data}")

    # Your logic here.
    tokenAddress = ""
    sell_token(tokenAddress)
    # wallet -= 1

def sell_token(tokenAddress):
    SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"  # Replace with your Solana RPC URL
    PRIVATE_KEY_BASE58 = ""  # Replace with your private key
    FROM_TOKEN_MINT = Pubkey.from_string("So11111111111111111111111111111111111111112")  # SOL
    client = Client(SOLANA_RPC_URL)
    private_key = keypair.Keypair.from_base58_string(PRIVATE_KEY_BASE58)
    public_key = private_key.pubkey()
    mint_key = Pubkey.from_string(tokenAddress)
    # balance = get_altcoin_balance(client,owner_pubkey=public_key,altcoin_mint_address="6V4TgjgAmDHPSW4kgFjegnhHaSk4eBeydZdRxjNhpump")
    # print(balance)
    token_account = client.get_token_accounts_by_owner(public_key, TokenAccountOpts(mint=mint_key))
    token_account_pubkey = token_account.value[0].pubkey

    balance = client.get_token_account_balance(token_account_pubkey)
    # print(f"Token Account: {token_account}, Balance: {balance.value.ui_amount}")  # balance.value.amount
    # print(balance)
    quote = get_jupiter_swap_quote(mint_key, FROM_TOKEN_MINT, balance.value.amount)
    execute_jupiter_swap(PRIVATE_KEY_BASE58, quote)
    print("Swap complete for: ", tokenAddress)
def get_jupiter_swap_quote(from_token_mint, to_token_mint, amount, slippage_bps=50):
    """Gets a swap quote from Jupiter."""
    url = f"https://api.jup.ag/swap/v1/quote?inputMint={from_token_mint}&outputMint={to_token_mint}&amount={amount}&slippageBps={slippage_bps}"
    response = requests.get(url)
    response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
    return response.json()
def execute_jupiter_swap(private_key_base58, quote_response,SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"):
    """Executes a swap using the Jupiter swap API."""
    client = Client(SOLANA_RPC_URL) #ASyncClient
    keypair_ = keypair.Keypair.from_base58_string(private_key_base58)
    user_address = keypair_.pubkey()

    # Get the swap transaction
    swap_transaction = requests.post(
        "https://api.jup.ag/swap/v1/swap",
        headers={"Content-Type": "application/json"},
        json={
            "quoteResponse": quote_response,  # Include the entire quoteResponse
            "userPublicKey": str(user_address),
            "wrapUnwrapSOL": True,
            "dynamicComputeUnitLimit": True,  # Add additional parameters
            "dynamicSlippage": True,
            "prioritizationFeeLamports": {
                "priorityLevelWithMaxLamports": {
                    "maxLamports": 1000000,
                    "priorityLevel": "veryHigh"
                }
            }
        },
    )
    swap_transaction.raise_for_status()
    swap_transaction_data = swap_transaction.json()

    tx_base64 = swap_transaction_data["swapTransaction"]
    tx = VersionedTransaction.from_bytes(base64.b64decode(tx_base64))

    # Sign and send the transaction
    try:
        signature = keypair_.sign_message(message.to_bytes_versioned(tx.message))
        signed_tx = VersionedTransaction.populate(tx.message,[signature])
        opts = TxOpts(skip_preflight=False, preflight_commitment=Processed)
        sent_tx = client.send_raw_transaction(txn=bytes(signed_tx),opts = opts)
        print(f"Transaction signature: {sent_tx}")
        transaction_id = json.loads(sent_tx.to_json())['result']
        print(f"Transaction sent: https://explorer.solana.com/tx/{transaction_id}")
    except Exception as e:
        print(f"Error executing swap: {e}")
