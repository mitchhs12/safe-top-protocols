import pandas as pd
import os
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from web3 import Web3
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()

# ---  CONFIGURATION  ---
INPUT_CSV = '../data/top_interacted_contracts_with_labels_and_types.csv'
OUTPUT_CSV = '../data/top_interacted_contracts_with_labels_and_types_and_symbols.csv'
ETHEREUM_RPC_URL = os.getenv('ETHEREUM_RPC_URL')

# --- OPTIMIZATION SETTINGS ---
# Number of concurrent threads to use. Start with 10 and increase if stable.
MAX_WORKERS = 10
# Maximum requests per second to avoid hitting API rate limits.
# Infura's free tier can handle more, but 10 is a safe starting point.
REQUESTS_PER_SECOND = 10

# A minimal description of the 'symbol()' function for web3.py
MINIMAL_ERC20_ABI = [{"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"payable":False,"stateMutability":"view","type":"function"}]


class RateLimiter:
    """A simple token bucket rate limiter to control request frequency."""
    def __init__(self, requests_per_second: int):
        self.requests_per_second = requests_per_second
        self._lock = threading.Lock()
        self._tokens = requests_per_second
        self._last_refill_time = time.monotonic()

    def wait(self):
        with self._lock:
            now = time.monotonic()
            time_since_refill = now - self._last_refill_time
            
            # Refill tokens based on elapsed time
            new_tokens = time_since_refill * self.requests_per_second
            if new_tokens > 0:
                self._tokens = min(self._tokens + new_tokens, self.requests_per_second)
                self._last_refill_time = now

            if self._tokens >= 1:
                self._tokens -= 1
            else:
                # Wait until a new token is available
                time.sleep(1 / self.requests_per_second)


def get_token_symbol(w3: Web3, contract_address: str, rate_limiter: RateLimiter) -> str:
    """
    Calls the symbol() function of an ERC20 contract, with rate limiting.
    """
    try:
        rate_limiter.wait() # Wait for our turn to make a request
        checksum_address = Web3.to_checksum_address(contract_address)
        contract = w3.eth.contract(address=checksum_address, abi=MINIMAL_ERC20_ABI)
        symbol = contract.functions.symbol().call()
        return symbol
    except Exception:
        return "Symbol not found"

def process_row(args):
    """Worker function for each thread to process a single row of the DataFrame."""
    index, row, w3, rate_limiter = args
    symbol = 'N/A'
    if row['contract_type'] == 'ERC20 Token':
        symbol = get_token_symbol(w3, row['destination_contract'], rate_limiter)
    return index, symbol


def main():
    """
    Main function to read a CSV, fetch token symbols concurrently, and save a new CSV.
    """
    if not ETHEREUM_RPC_URL:
        print("Error: ETHEREUM_RPC_URL environment variable is not set.")
        return

    try:
        df = pd.read_csv(INPUT_CSV)
        print(f"Successfully read '{INPUT_CSV}' with {len(df)} rows.")
    except FileNotFoundError:
        print(f"Error: The input file '{INPUT_CSV}' was not found.")
        return

    w3 = Web3(Web3.HTTPProvider(ETHEREUM_RPC_URL))
    if not w3.is_connected():
        print(f"Error: Could not connect to Ethereum node at {ETHEREUM_RPC_URL}")
        return
    print(f"Successfully connected to Ethereum node. Starting concurrent processing with {MAX_WORKERS} workers.")
    
    rate_limiter = RateLimiter(REQUESTS_PER_SECOND)
    tasks = [(index, row, w3, rate_limiter) for index, row in df.iterrows()]
    
    # Pre-fill the results list with placeholders
    results = [''] * len(df)
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Use tqdm to create a progress bar
        future_results = executor.map(process_row, tasks)
        for index, symbol in tqdm(future_results, total=len(tasks), desc="Fetching Symbols"):
            # Place the result in the correct position
            results[index] = symbol
            
    # Add the results as a new column
    df['token_symbol'] = results
    print("\nSymbol fetching complete.")

    # Save the final results to a new file
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"Successfully saved final data to '{OUTPUT_CSV}'.")


if __name__ == "__main__":
    main()