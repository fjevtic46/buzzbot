import functions_framework
import os
from google.cloud import functions_v2
import time
import requests

@functions_framework.cloud_event
def main(cloud_event):
    data = cloud_event.data
    user_id = os.environ.get("USER_ID")
    trigger_function_3 = os.environ.get("FUNCTION_TRIGGER_3")

    print(f"Trigger function 2 for user: {user_id} triggered with data: {data}")

    # Your logic here.
    tokenAddress = "INSERT TOKEN ADDRESS"
    tokenMetaData = "INSERT TOKEN METADATA"
    while(True):
        tokenLiveData = get_pricehistory_dexscreener(tokenAddress)[0]
        condition_count = 0
        if (tokenMetadata['priceNative'] * 0.92) <= float(tokenLiveData['priceNative']):
            condition_count += 1
            # valid_token_dict[tokenAddress]['priceNative'] = float(tokenLiveData['priceNative'])
        if tokenMetadata['m5_buys'] <= tokenLiveData['txns']['m5']['buys']:
            condition_count += 1
            # valid_token_dict[tokenAddress]['m5_buys'] = tokenLiveData['txns']['m5']['buys']
        if tokenMetadata['m5_buysell_ratio'] <= tokenLiveData['txns']['m5']['buys'] / tokenLiveData['txns']['m5'][
            'sells']:
            condition_count += 1
        if tokenMetadata['m5_volume'] <= tokenLiveData['volume']['m5']:
            condition_count += 1
            # valid_token_dict[tokenAddress]['m5_volume'] = tokenLiveData['2volume']['m5']
        if condition_count == 0:
            client = functions_v2.FunctionServiceClient()
            request = functions_v2.InvokeFunctionRequest(name=f"projects/{os.environ.get('PROJECT_ID')}/locations/{os.environ.get('REGION')}/functions/{trigger_function_3}")
            response = client.invoke_function(request=request)

            print(f"Triggered function 3 for user: {user_id}")
            return "Function 2 executed."

        time.sleep(60)

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