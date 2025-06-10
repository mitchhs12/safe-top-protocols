import os
import pandas as pd
from dune_client.client import DuneClient
from dune_client.query import Query

# Make sure your DUNE_API_KEY is set as an environment variable
# In your terminal: export DUNE_API_KEY="your_api_key_here"
api_key = os.environ.get("DUNE_API_KEY")
if not api_key:
    raise ValueError("DUNE_API_KEY environment variable not set!")

# Your SQL query
sql_query = """
SELECT
  COUNT(*) AS num_safes
FROM safe_ethereum.safes
"""

# Create a query object
query = Query(
    name="Total Number of Safe Wallets",
    query=sql_query
)

# Initialize the Dune client
dune = DuneClient(api_key)

try:
    # Execute the query and get the results
    print("Executing query on Dune...")
    results = dune.run_query(query)

    # The results are in results.result.rows, which is a list of dictionaries
    # We can load this directly into a pandas DataFrame
    df = pd.DataFrame(results.result.rows)

    # Define the output filename
    output_filename = "safe_wallet_count.csv"

    # Save the DataFrame to a CSV file
    # index=False prevents pandas from writing the DataFrame index as a column
    df.to_csv(output_filename, index=False)

    print(f"✅ Success! Results saved to {output_filename}")
    print("\n--- Data ---")
    print(df.to_string())


except Exception as e:
    print(f"An error occurred: {e}")