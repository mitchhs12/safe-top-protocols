import pandas as pd
import os

def filter_erc20_tokens():
    """
    Reads the final data CSV, filters out ERC20 tokens,
    and saves the result to a new CSV file.
    """
    # Define file paths
    input_csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'final_data.csv')
    output_csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'filtered_protocols.csv')

    # Read the CSV file into a pandas DataFrame
    try:
        df = pd.read_csv(input_csv_path)
        print(f"Successfully loaded {input_csv_path}. Shape: {df.shape}")
    except FileNotFoundError:
        print(f"Error: The file {input_csv_path} was not found.")
        return

    # Filter out rows where 'contract_type' is 'ERC20 Token'
    initial_rows = len(df)
    filtered_df = df[df['contract_type'] != 'ERC20 Token'].copy()
    final_rows = len(filtered_df)

    print(f"Removed {initial_rows - final_rows} rows corresponding to ERC20 tokens.")

    # Save the filtered DataFrame to a new CSV file
    filtered_df.to_csv(output_csv_path, index=False)
    print(f"Filtered data saved to {output_csv_path}. New shape: {filtered_df.shape}")

if __name__ == "__main__":
    filter_erc20_tokens()
