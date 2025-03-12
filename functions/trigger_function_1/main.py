#Function Deployment: Zip the function code directories (e.g., trigger_function_1) and upload them to your GCS source bucket.
import functions_framework
import os
from google.cloud import functions_v2

import base64
import json
import requests
from solana.rpc.api import Client
from solana.rpc.api import Pubkey
from solana.rpc.api import VersionedTransaction
from solders import keypair
from solders import message
from solana.rpc.types import TxOpts
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed

@functions_framework.cloud_event
def main(cloud_event):
    data = cloud_event.data
    user_id = os.environ.get("USER_ID")
    trigger_function_2 = os.environ.get("FUNCTION_TRIGGER_2")

    print(f"Trigger function 1 for user: {user_id} triggered with data: {data}")

    tokenAddress = "INSERT TOKEN ADDRESS"
    purchase_token(tokenAddress)

    client = functions_v2.FunctionServiceClient()
    request = functions_v2.InvokeFunctionRequest(name=f"projects/{os.environ.get('PROJECT_ID')}/locations/{os.environ.get('REGION')}/functions/{trigger_function_2}")
    response = client.invoke_function(request=request)

    print(f"Triggered function 2 for user: {user_id}")
    return "Function 1 executed."
def purchase_token(tokenAddress):
    # Config ####################################
    SOLANA_RPC_URL = "https://api.mainnet-beta.solana.com"  # Replace with your Solana RPC URL
    PRIVATE_KEY_BASE58 = ""  # Replace with your private key in base58
    FROM_TOKEN_MINT = Pubkey.from_string("So11111111111111111111111111111111111111112")  # SOL
    # TO_TOKEN_MINT = Pubkey.from_string("4ufd8JtAY1vMGPeAHAbNhztJoVgqSMiiK3EFpsmopump")
    AMOUNT_IN_SOL = 0.03  # Amount of SOL to swap
    ############################################
    TO_TOKEN_MINT = Pubkey.from_string(tokenAddress) # Replace with the altcoin's mint address
    swap_token(TO_TOKEN_MINT=TO_TOKEN_MINT, FROM_TOKEN_MINT = FROM_TOKEN_MINT, AMOUNT_IN_SOL=AMOUNT_IN_SOL)


def swap_token(TO_TOKEN_MINT, FROM_TOKEN_MINT, AMOUNT_IN_SOL=0.02):
    # Config
    PRIVATE_KEY_BASE58 = ""
    try:
        amount_in_lamports = int(AMOUNT_IN_SOL * 10**9) #Convert SOL to lamports
        quote = get_jupiter_swap_quote(FROM_TOKEN_MINT, TO_TOKEN_MINT, amount_in_lamports)
        execute_jupiter_swap(PRIVATE_KEY_BASE58, quote)
    except requests.exceptions.RequestException as e:
        print(f"API request error: {e}")
    except Exception as generic_error:
        print(f"An unexpected error occurred: {generic_error}")
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