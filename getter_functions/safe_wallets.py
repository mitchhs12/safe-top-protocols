import os
import pandas as pd
from dune_client.client import DuneClient
from dune_client.query import QueryBase 
from dotenv import load_dotenv

load_dotenv()

# --- Environment variables ---
DUNE_API_KEY = os.environ.get("DUNE_API_KEY")
QUERY_ID = os.environ.get("ALL_SAFES_QUERY")
if not DUNE_API_KEY and not QUERY_ID:
    raise ValueError("DUNE_API_KEY and QUERY_ID not found. Please set it as an environment variable.")

# --- Define the query using QueryBase ---
wallet_count_query = QueryBase(
    query_id=QUERY_ID,
)

# Initialize the Dune client
dune = DuneClient(DUNE_API_KEY)

try:
    # --- Execute query and get results as a Pandas DataFrame ---
    print("Executing query on Dune...")
    results_df = dune.run_query_dataframe(query=wallet_count_query)

    # --- Save the DataFrame to a CSV file ---
    output_filename = '../data/safe_wallet_count.csv'
    results_df.to_csv(output_filename, index=False)
    
    print(f"✅ Successfully saved query results to {output_filename}")
    print("\nFile content:")
    print(results_df.to_string(index=False))

except Exception as e:
    print(f"An error occurred: {e}")