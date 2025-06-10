import os
import pandas as pd
from dune_client.client import DuneClient
from dune_client.query import QueryBase 
from dotenv import load_dotenv

load_dotenv()

# --- Setup ---
DUNE_API_KEY = os.environ.get("DUNE_API_KEY")
QUERY_ID = os.environ.get("TOP_CONTRACTS_QUERY")

if not DUNE_API_KEY and not QUERY_ID:
    raise ValueError("DUNE_API_KEY and QUERY_ID not found. Please set it as an environment variable.")

top_10_query = QueryBase(
    query_id=QUERY_ID
)

dune = DuneClient(DUNE_API_KEY)

try:
    # --- Fetch the final results from Dune ---
    print("Executing query on Dune to find top contracts...")
    results_df = dune.get_latest_result_dataframe(query=top_10_query)

    # --- Save the final list to a new CSV file ---
    output_filename = '../data/top_interacted_contracts.csv'
    results_df.to_csv(output_filename, index=False)
    
    print(f"✅ Success! The Top list has been saved to {output_filename}")
    print("\nFile content:")
    print(results_df.to_string(index=False))

except Exception as e:
    print(f"An error occurred: {e}")