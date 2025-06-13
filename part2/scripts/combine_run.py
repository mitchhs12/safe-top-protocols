import os
import pandas as pd

# --- Configuration ---
DIRECT_TXS_PATH = '../data/all_contracts_excluding_multisends.csv'
MULTISEND_TXS_PATH = '../data/decoded.csv'
OUTPUT_CSV_PATH = '../data/final_combined.csv'

def main():
    """
    Combines direct interaction counts with multisend interaction counts
    to create a final, aggregated report with just the address and total count.
    """
    print("Reading source CSV files...")
    if not os.path.exists(DIRECT_TXS_PATH) or not os.path.exists(MULTISEND_TXS_PATH):
        print("Error: Ensure both input files exist:")
        print(f"1. {DIRECT_TXS_PATH}")
        print(f"2. {MULTISEND_TXS_PATH}")
        return

    df_direct = pd.read_csv(DIRECT_TXS_PATH)
    df_multisend = pd.read_csv(MULTISEND_TXS_PATH)

    # --- CHANGE: Normalize all address columns to lowercase right after loading ---
    print("Normalizing addresses to lowercase...")
    # Check if the column exists before trying to modify it
    if 'destination_contract' in df_direct.columns:
        df_direct['destination_contract'] = df_direct['destination_contract'].str.lower()
    
    if 'forwarded_to_address' in df_multisend.columns:
        df_multisend['forwarded_to_address'] = df_multisend['forwarded_to_address'].str.lower()
    # --- END OF CHANGE ---

    print("Aggregating decoded multisend transaction counts...")
    
    # 1. Count the occurrences of each forwarded address from the multisend data
    multisend_counts = df_multisend['forwarded_to_address'].value_counts().reset_index()
    multisend_counts.columns = ['destination_contract', 'multisend_interaction_count']

    print("Merging direct and multisend interaction data...")

    # 2. Merge the two dataframes using an 'outer' join
    # This will now work correctly because the 'destination_contract' key is lowercase in both.
    df_merged = pd.merge(
        df_direct,
        multisend_counts,
        on='destination_contract',
        how='outer'
    )

    # 3. Fill NaN values with 0 for counts
    df_merged['interaction_count'] = df_merged['interaction_count'].fillna(0).astype(int)
    df_merged['multisend_interaction_count'] = df_merged['multisend_interaction_count'].fillna(0).astype(int)
    
    print("Calculating final totals...")

    # 4. Calculate the new total interaction count
    df_merged['total_interaction_count'] = df_merged['interaction_count'] + df_merged['multisend_interaction_count']

    # 5. Finalize the dataframe for the report
    final_df = df_merged[['destination_contract', 'total_interaction_count']].copy()

    final_df.rename(columns={
        'destination_contract': 'address',
        'total_interaction_count': 'amount_of_times_interacted_with'
    }, inplace=True)

    # Sort by the new total count
    final_df.sort_values(by='amount_of_times_interacted_with', ascending=False, inplace=True)

    # Ensure parent directory exists and save to CSV
    os.makedirs(os.path.dirname(OUTPUT_CSV_PATH), exist_ok=True)
    final_df.to_csv(OUTPUT_CSV_PATH, index=False)

    print(f"\n✅ Success! Final combined report has been created.")
    print(f"Results saved to {OUTPUT_CSV_PATH}")
    print("\n--- Sample of Final Combined Data ---")
    print(final_df.head(10).to_string(index=False))

if __name__ == "__main__":
    main()