import pandas as pd
import requests
import time
import os
import json
from dotenv import load_dotenv

load_dotenv()

# --- Configuration ---
API_KEY = os.getenv('ETHERSCAN_API_KEY')
INPUT_CSV = '../data/top_interacted_contracts.csv'
OUTPUT_CSV = '../data/top_interacted_contracts_with_labels_and_types.csv'
API_URL = 'https://api.etherscan.io/api'

# --- ERC20 Standard Definition ---
ERC20_REQUIRED_FUNCTIONS = {
    "totalSupply", "balanceOf", "transfer", "transferFrom", "approve", "allowance"
}
ERC20_REQUIRED_EVENTS = {"Transfer", "Approval"}

def check_abi_for_erc20(abi_string: str) -> str:
    """Helper function to check if a given ABI is ERC20 compliant."""
    if not abi_string or abi_string == 'Contract source code not verified':
        return "Not a Verified Contract"
    
    try:
        abi = json.loads(abi_string)
        functions = {item['name'] for item in abi if item['type'] == 'function'}
        events = {item['name'] for item in abi if item['type'] == 'event'}
        
        if ERC20_REQUIRED_FUNCTIONS.issubset(functions) and ERC20_REQUIRED_EVENTS.issubset(events):
            return "ERC20 Token"
        else:
            return "Other Contract"
    except json.JSONDecodeError:
        return "ABI Parse Error"

def get_contract_info(address: str) -> dict:
    """
    Fetches contract name and type, resolving proxies to check the implementation contract.
    """
    info = {"label": "N/A", "type": "N/A"}
    
    try:
        # Initial API call for the given address
        params = {'module': 'contract', 'action': 'getsourcecode', 'address': address, 'apikey': API_KEY}
        response = requests.get(API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if data['status'] == '0':
            info['label'] = data.get('result', 'API Error: No result')
            info['type'] = 'API Error'
            return info

        result = data['result'][0]
        info['label'] = result.get('ContractName') or "Label not found"
        implementation_address = result.get('Implementation')

        # Check if it's a proxy by looking for the 'Implementation' field
        if implementation_address:
            print(f"  -> Proxy detected. Implementation: {implementation_address}")
            # This is a proxy. We need to fetch the ABI of the implementation contract.
            time.sleep(0.25) # Add a small delay before the second API call
            
            # 3. Make a SECOND API call for the implementation contract
            imp_params = {'module': 'contract', 'action': 'getsourcecode', 'address': implementation_address, 'apikey': API_KEY}
            imp_response = requests.get(API_URL, params=imp_params)
            imp_response.raise_for_status()
            imp_data = imp_response.json()
            
            if imp_data['status'] == '1':
                implementation_abi = imp_data['result'][0]['ABI']
                info['type'] = check_abi_for_erc20(implementation_abi)
            else:
                info['type'] = "Proxy to Unverified Implementation"
        else:
            # 4. Not a proxy, just check its own ABI
            own_abi = result.get('ABI')
            info['type'] = check_abi_for_erc20(own_abi)

    except requests.exceptions.RequestException as e:
        print(f"  -> API Request Error for {address}: {e}")
        info['label'] = "API Request Error"
        info['type'] = "API Request Error"
    except (KeyError, IndexError) as e:
        print(f"  -> Response Parse Error for {address}: {e}")
        info['label'] = "Response Parse Error"
        info['type'] = "Response Parse Error"
        
    return info

def main():
    if not API_KEY:
        print("Error: ETHERSCAN_API_KEY environment variable not set.")
        return
    try:
        df = pd.read_csv(INPUT_CSV)
    except FileNotFoundError:
        print(f"Error: The input file '{INPUT_CSV}' was not found.")
        return

    labels = []
    contract_types = []
    total = len(df)
    print(f"Found {total} addresses to process. Starting...")

    for index, row in df.iterrows():
        address = row['destination_contract']
        print(f"({index + 1}/{total}) Processing: {address}")
        
        # This function now handles the proxy logic internally
        info = get_contract_info(address)
        
        labels.append(info['label'])
        contract_types.append(info['type'])
        
        print(f"  -> Label: {info['label']}, Type: {info['type']}")
        
        time.sleep(0.25) # Main rate-limiting delay for Etherscan Free API

    df['label'] = labels
    df['contract_type'] = contract_types
    df.to_csv(OUTPUT_CSV, index=False)
    
    print(f"\nProcessing complete! Data saved to '{OUTPUT_CSV}'.")

if __name__ == "__main__":
    main()