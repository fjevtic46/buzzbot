import os
import time
import requests
import json
import base64
from google.cloud import secretmanager, functions_v2
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

def get_latest_tokens_dexscreener():
    """Fetches real-time latest tokens from Dex Screener"""
    url = "https://api.dexscreener.com/token-profiles/latest/v1"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        return data
    except requests.exceptions.RequestException as e:
        error = f"Error fetching data: {e}"
        # log error
        return error
def filter_dexscreener_data(data):
    '''
    Filter tokens from dex screener to only valid ones.
    :param data: List
    :return: valid_tokens: List
    '''
    valid_tokens = []
    for token in data:
        valid,passed_tests = is_valid_dexscreener(token)
        if valid:
            valid_tokens.append((token,passed_tests))
    return valid_tokens
def is_valid_dexscreener(tokenMetadata):
    '''
    Determines if dexscreener token is valid for purchase.
    :param tokenMetadata: Dict
    :return: valid: Boolean
    '''
    if tokenMetadata['chainId'] != "solana":
        return False,[]

    score_sum = 0
    passed_tests = []

    if check_pool_dexscreener(pool_data= get_pool_dexscreener(tokenAddress=tokenMetadata['tokenAddress'])):
        score_sum += 1
        passed_tests.append('pool_test')
    if check_orderspaid_dexscreener(orders_data= get_orderspaid_dexscreener(tokenAddress=tokenMetadata['tokenAddress'])):
        score_sum += 1
        passed_tests.append('orders_test')
    if check_links(tokenMetadata = tokenMetadata):
        score_sum += 1
        passed_tests.append('link_test')
    if check_pricehistory_dexscreener(token_data = get_pricehistory_dexscreener(tokenAddress=tokenMetadata['tokenAddress'])):
        score_sum += 1
        passed_tests.append('pricehistory_test')
    if score_sum == 3:
        return True,passed_tests
    else:
        return False,passed_tests
def check_links(tokenMetadata):
    if 'links' in tokenMetadata:
        if len(tokenMetadata['links']) >= 2:
            return True
    return False
def get_pool_dexscreener(tokenAddress,chainId = "solana"):
    '''
    Retrieves the pool data for a token.
    :param pair_address: str
    :return: Pool Data: list
    '''
    response = requests.get(
        f"https://api.dexscreener.com/token-pairs/v1/{chainId}/{tokenAddress}",
    )
    data = response.json()
    return data
def get_orderspaid_dexscreener(tokenAddress, chainId = "solana"):
    '''
    Get data on orders paid for a token. Determines level of advertising
    and helps determine if it's a pump and dump scheme.
    :param pair_address: str
    :param chainId: str
    :return: List
    '''

    response = requests.get(
        f"https://api.dexscreener.com/orders/v1/{chainId}/{tokenAddress}",
    )

    data = response.json()
    return data
def get_pricehistory_dexscreener(tokenAddress,chainId = "solana"):
    '''
    Get Price History Data for a specific token.
    :param tokenAddress: str
    :param chainId: str
    :return: List
    '''

    # data = response.json()
    # return data
    retries = 3

    for i in range(retries):
        try:
            response = requests.get(
                f"https://api.dexscreener.com/tokens/v1/{chainId}/{tokenAddress}"
                # DuypYwg2mr5hD9iPJCxiYSEvA4t9dFFGSU2HmF9vFCWu"
            )
            response.raise_for_status()
            data = response.json()
            return data
            # break  # Success, exit the loop
        except Exception as e:
            print(f"Attempt {i + 1} failed: {e}")
            if i < retries - 1:
                time.sleep(2)  # 2-second delay between retries
            else:
                print("Failed after retries.")
def check_pool_dexscreener(pool_data,
                           min_liquidity_usd=100000,
                           min_pool_age_days=7,
                           min_volume_usd=10000,
                           max_price_change_percent=20,
                           min_num_pools=2,
                           max_fdv_usd=1000000):
    '''
    Determines if a token is a safe buy based on its liquidity pool data.

    Args:
        pool_data (list): A list of dictionaries containing pool data from Dex Screener's API.
        min_liquidity_usd (float): The minimum liquidity in USD required for a safe buy.
        min_pool_age_days (int): The minimum age of the pool in days required for a safe buy.
        min_volume_usd (float): The minimum 24-hour volume in USD required for a safe buy.
        max_price_change_percent (float): The maximum allowed price change percentage in the last 24 hours.
        min_num_pools (int): The minimum number of pools the token should be in.
        max_fdv_usd (float): The maximum allowed fully diluted market cap in USD.

    Returns:
        bool: True if the token is a safe buy, False otherwise.
    '''


    # Check if there are enough pools
    if len(pool_data) < min_num_pools:
        return False

    # Check each pool for various criteria
    safe_pools = 0
    for pool in pool_data:
        if 'liquidity' not in pool or 'pairCreatedAt' not in pool or 'priceChange' not in pool or 'volume' not in pool:
            continue
        liquidity_usd = pool["liquidity"]["usd"]
        pool_age_seconds = time.time() - pool["pairCreatedAt"]
        pool_age_days = pool_age_seconds / (60 * 60 * 24)
        volume_usd = pool["volume"].get("h24", 0)  # Use 0 if h24 volume is not available
        price_change_percent = abs(pool["priceChange"].get("h24",
                                                          0)) * 100  # Use 0 if h24 price change is not available
        fdv_usd = pool.get("fdv", 0)  # Use 0 if fdv is not available

        if (liquidity_usd >= min_liquidity_usd and pool_age_days >= min_pool_age_days and
                volume_usd >= min_volume_usd and price_change_percent <= max_price_change_percent and
                fdv_usd <= max_fdv_usd):
            safe_pools += 1

    # Check if enough pools met the criteria
    return safe_pools >= min_num_pools
def check_orderspaid_dexscreener(orders_data,
                                 max_recent_ads=2,
                                 max_recent_takeovers=1,
                                 ad_window_hours=24,
                                 takeover_window_hours=72):
    '''
    Determines if a token is legitimate based on its paid orders data.

    Args:
        orders_data (list): A list of dictionaries containing paid orders data from Dex Screener's API.
        max_recent_ads (int): The maximum number of recent token ads allowed for a legitimate token.
        max_recent_takeovers (int): The maximum number of recent community takeovers allowed.
        ad_window_hours (int): The time window in hours for considering recent token ads.
        takeover_window_hours (int): The time window in hours for considering recent takeovers.

    Returns:
        bool: True if the token is likely legitimate, False otherwise.
    '''
    if not orders_data:
        return True  # No paid orders data, assume legitimate for now

    now = time.time() * 1000  # Current time in milliseconds
    recent_ads = 0
    recent_takeovers = 0

    for order in orders_data:
        if "type" not in order or "status" not in order:
            continue
        if order["type"] == "tokenAd" and order["status"] == "approved":
            if now - order["paymentTimestamp"] <= ad_window_hours * 60 * 60 * 1000:
                recent_ads += 1
        elif order["type"] == "communityTakeover" and order["status"] == "approved":
            if now - order[
                "paymentTimestamp"] <= takeover_window_hours * 60 * 60 * 1000:
                recent_takeovers += 1

    return recent_ads <= max_recent_ads and recent_takeovers <= max_recent_takeovers
def check_pricehistory_dexscreener(token_data,
                        min_m5_buy_ratio = 0.8,
                        min_h1_buy_ratio=1.2,
                         min_h6_buy_ratio=1.1,
                         max_m5_price_drop_percent=5,
                         min_m5_volume = 500,
                         min_liquidity_usd=100000,
                         min_pool_age_days=7,
                         min_volume_usd=10000,
                         max_price_change_percent=20,
                         min_num_pools=2,
                         max_fdv_usd=1000000):
        """
        Determines if a token should be bought based on various criteria.

        Args:
            token_data (list): A list of dictionaries containing token data from Dex Screener's API.
            min_h1_buy_ratio (float): The minimum ratio of buys to sells in the last hour.
            min_h6_buy_ratio (float): The minimum ratio of buys to sells in the last 6 hours.
            max_m5_price_drop_percent (float): The maximum allowed price drop percentage in the last 5 minutes.
            min_liquidity_usd (float): The minimum liquidity in USD required for a safe buy.
            min_pool_age_days (int): The minimum age of the pool in days required for a safe buy.
            min_volume_usd (float): The minimum 24-hour volume in USD required for a safe buy.
            max_price_change_percent (float): The maximum allowed price change percentage in the last 24 hours.
            min_num_pools (int): The minimum number of pools the token should be in.
            max_fdv_usd (float): The maximum allowed fully diluted market cap in USD.

        Returns:
            bool: True if the token should be bought, False otherwise.
        """

        if not token_data:
            return False

        token = token_data[0]  # Assuming only one token's data is provided

        # Check buy/sell ratios
        if token["txns"]["m5"]["sells"] == 0 or token["txns"]["h1"]["sells"] == 0 or token["txns"]["h6"]["sells"] == 0:
            return False
        m5_buy_ratio = token["txns"]["m5"]["buys"] / token["txns"]["m5"]["sells"]
        h1_buy_ratio = token["txns"]["h1"]["buys"] / token["txns"]["h1"]["sells"]
        h6_buy_ratio = token["txns"]["h6"]["buys"] / token["txns"]["h6"]["sells"]
        if m5_buy_ratio < min_m5_buy_ratio or h1_buy_ratio < min_h1_buy_ratio or h6_buy_ratio < min_h6_buy_ratio:
            return False

        # Check recent price drop
        m5_price_drop_percent = token["priceChange"].get("m5",0)
        if m5_price_drop_percent < -max_m5_price_drop_percent:
            return False
        m5_volume = token["volume"].get("m5",0)
        if m5_volume < min_m5_volume:
            return False



        # All checks passed, so the token should be bought
        return True
def checkWalletSize():
    walletTokenLimit = 5
    userID = 0

    # Use application default credentials
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)

    db = firestore.client()
    doc_ref = db.collection("user").document(str(userID))
    data = doc_ref.get().to_dict()
    walletSize = 5
    if walletSize <= walletTokenLimit:
        return True
    # get wallet size
    return False
def main():
    project_id = os.environ.get("PROJECT_ID")
    region = os.environ.get("REGION")
    function_trigger_1 = os.environ.get("FUNCTION_TRIGGER_1")
    user_id = os.environ.get("USER_ID")

    while True:
        try:
            # Fetch API data (token List)
            api_data = get_latest_tokens_dexscreener()
            # Filter API data
            valid_tokens = filter_dexscreener_data(api_data)
            # Loop through each valid token and purchase if wallet not full
            for token in valid_tokens:
                valid_token_dict = dict()
                # Trigger condition
                if token[0]['tokenAddress'] not in valid_token_dict and checkWalletSize():
                    valid_token_dict[token[0]['tokenAddress']] = dict()
                    tokenData = get_pricehistory_dexscreener(token[0]['tokenAddress'])[0]
                    valid_token_dict[token[0]['tokenAddress']]['priceNative'] = float(tokenData['priceNative'])
                    valid_token_dict[token[0]['tokenAddress']]['m5_buys'] = tokenData['txns']['m5']['buys']
                    valid_token_dict[token[0]['tokenAddress']]['m5_buysell_ratio'] = tokenData['txns']['m5'][
                                                                                         'buys'] / \
                                                                                     tokenData['txns']['m5'][
                                                                                         'sells']
                    valid_token_dict[token[0]['tokenAddress']]['m5_volume'] = tokenData['volume']['m5']
                    valid_token_dict[token[0]['tokenAddress']]['m5_priceChange'] = tokenData['priceChange']

                    # ts.purchase_token(token[0]['tokenAddress'])
                    print(f"Trigger condition met for user: {user_id}")
                    client = functions_v2.FunctionServiceClient()
                    request = functions_v2.InvokeFunctionRequest(
                        name=f"projects/{project_id}/locations/{region}/functions/{function_trigger_1}")
                    response = client.invoke_function(request=request)
                    print(f"Function {function_trigger_1} triggered for user: {user_id}")
                    # += 1 wallet size

            else:
              print(f"Trigger condition not met for user: {user_id}")

        except Exception as e:
            print(f"Error in start-service for user: {user_id}: {e}")

        time.sleep(300) # 5 minutes (300 seconds)

if __name__ == "__main__":
    main()