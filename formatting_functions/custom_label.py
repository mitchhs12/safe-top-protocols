import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()


# --- CONFIGURATION ---

# Define the paths to your input and output files
MAIN_FILE_PATH = '../data/top_interacted_contracts_with_labels_and_types_and_symbols.csv'
ACCOUNTS_LABELS_PATH = '../eth_labels/accounts.csv'
TOKENS_LABELS_PATH = '../eth_labels/tokens.csv'
OUTPUT_FILE_PATH = '../data/final_data.csv'

# --- SCRIPT ---

def main():
    """
    Reads a main CSV and enriches it with labels from two other CSVs.
    """
    print("Starting the data enrichment process...")

    # 1. Load all three CSV files into pandas DataFrames
    try:
        main_df = pd.read_csv(MAIN_FILE_PATH)
        accounts_df = pd.read_csv(ACCOUNTS_LABELS_PATH)
        tokens_df = pd.read_csv(TOKENS_LABELS_PATH)
        print("Successfully loaded all input CSV files.")
    except FileNotFoundError as e:
        print(f"Error: Could not find a file. Please check your paths. Details: {e}")
        return

    # 2. Normalize addresses to lowercase for reliable matching
    main_df['lookup_address'] = main_df['destination_contract'].str.lower()
    accounts_df['address'] = accounts_df['address'].str.lower()
    tokens_df['address'] = tokens_df['address'].str.lower()

    # --- FIX: Handle duplicate addresses in the lookup files ---
    # Keep only the first occurrence of each address to ensure a unique index.
    accounts_df.drop_duplicates(subset=['address'], keep='first', inplace=True)
    tokens_df.drop_duplicates(subset=['address'], keep='first', inplace=True)
    print("Removed duplicate addresses from lookup files.")

    # 3. Create efficient lookup maps (dictionaries) from the label files
    accounts_map = accounts_df.set_index('address')['label']
    tokens_map = tokens_df.set_index('address')['label']
    print("Created lookup maps from accounts and tokens files.")

    # 4. Map the labels to your main DataFrame based on the lookup address
    labels_from_accounts = main_df['lookup_address'].map(accounts_map)
    labels_from_tokens = main_df['lookup_address'].map(tokens_map)
    
    # 5. Apply the priority rule using .combine_first()
    main_df['custom_label'] = labels_from_accounts.combine_first(labels_from_tokens)
    print("Applied priority logic to create the 'custom_label' column.")

    # 6. Clean up the temporary 'lookup_address' column
    main_df.drop(columns=['lookup_address'], inplace=True)
    
    # 7. Save the final enriched DataFrame to a new CSV file
    output_dir = os.path.dirname(OUTPUT_FILE_PATH)
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    main_df.to_csv(OUTPUT_FILE_PATH, index=False)
    print(f"\nProcess complete! Final data saved to '{OUTPUT_FILE_PATH}'.")


if __name__ == "__main__":
    main()