import os
from dune_client.client import DuneClient
from dune_client.query import QueryBase 
from dotenv import load_dotenv
import time

load_dotenv()

# --- Setup ---
DUNE_API_KEY = os.environ.get("DUNE_KEY")
QUERY_ID_ALL_TOTALS = os.environ.get("ALL_CONTRACTS")
QUERY_ID_MULTISEND_TOTALS = os.environ.get("MULTISEND_TRANSACTIONS")
QUERY_ID_TOTALS_WITHOUT_MULTISEND = os.environ.get("ALL_CONTRACTS_EXCLUDING_MULTISENDS")
print(DUNE_API_KEY, QUERY_ID_ALL_TOTALS, QUERY_ID_MULTISEND_TOTALS, QUERY_ID_TOTALS_WITHOUT_MULTISEND)
if not DUNE_API_KEY or not QUERY_ID_ALL_TOTALS or not QUERY_ID_MULTISEND_TOTALS or not QUERY_ID_TOTALS_WITHOUT_MULTISEND:
    print(f"DUNE_API_KEY: {DUNE_API_KEY}")
    print(f"QUERY_ID_ALL_TOTALS: {QUERY_ID_ALL_TOTALS}")
    print(f"QUERY_ID_MULTISEND_TOTALS: {QUERY_ID_MULTISEND_TOTALS}")
    print(f"QUERY_ID_TOTALS_WITHOUT_MULTISEND: {QUERY_ID_TOTALS_WITHOUT_MULTISEND}")

    raise ValueError("Please fix these environment variables:")
  

# Gets all contracts (multisend and non-multisend)
query_all = QueryBase(
    query_id=QUERY_ID_ALL_TOTALS
)

# Gets all multisend TRANSCATIONS
query_multisend = QueryBase(
    query_id=QUERY_ID_MULTISEND_TOTALS
)

# Gets all contracts that are not multisend contracts
query_totals_without_multisend = QueryBase(
    query_id=QUERY_ID_TOTALS_WITHOUT_MULTISEND
)

dune = DuneClient(DUNE_API_KEY)

try:
    # --- Execute the query and fetch the results ---
    print("Executing queries on Dune...")
    results_df = dune.run_query_dataframe(query=query_all)

    results_df_multisend = dune.run_query_dataframe(query=query_multisend)

    results_df_totals_without_multisend = dune.run_query_dataframe(query=query_totals_without_multisend)

    output_filename = '../data/all_contracts.csv'
    results_df.to_csv(output_filename, index=False)

    output_filename_multisend = '../data/multisend_transactions.csv'
    results_df_multisend.to_csv(output_filename_multisend, index=False)

    output_filename_totals_without_multisend = '../data/all_contracts_excluding_multisends.csv'
    results_df_totals_without_multisend.to_csv(output_filename_totals_without_multisend, index=False)
    
    print(f"✅ Success! The results have been saved.")

except Exception as e:
    print(f"An error occurred: {e}")