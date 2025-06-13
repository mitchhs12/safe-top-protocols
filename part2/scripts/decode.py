import os
import pandas as pd
from eth_abi import decode
from eth_utils import to_checksum_address, keccak

# --- Configuration ---
INPUT_CSV_PATH = '../data/multisend_transactions.csv'
OUTPUT_CSV_PATH = '../data/decoded.csv'

# --- Function Signatures and Selectors ---
EXEC_TX_SIGNATURE = 'execTransaction(address,uint256,bytes,uint8,uint256,uint256,uint256,address,address,bytes)'
MULTISEND_SIGNATURE = 'multiSend(bytes)'

EXEC_TX_SELECTOR = "0x" + keccak(text=EXEC_TX_SIGNATURE)[:4].hex()
NESTED_MULTISEND_SELECTOR = "0x" + keccak(text=MULTISEND_SIGNATURE)[:4].hex()


def decode_multisend_from_exec_tx(exec_tx_input: str) -> (list, str): # type: ignore
    """
    Decodes a multiSend call nested inside an execTransaction call.
    """
    if not isinstance(exec_tx_input, str) or not exec_tx_input.startswith(EXEC_TX_SELECTOR):
        # This case shouldn't happen with your data, but it's good practice.
        return [], "Input is not a valid execTransaction call."

    try:
        # Decode the outer execTransaction call
        exec_tx_abi_types = ['address', 'uint256', 'bytes']
        exec_tx_data_bytes = bytes.fromhex(exec_tx_input[10:])
        _, _, nested_data_bytes = decode(exec_tx_abi_types, exec_tx_data_bytes)

        # Check if the nested data is a multiSend call
        nested_data_hex = nested_data_bytes.hex()
        if not nested_data_hex.startswith(NESTED_MULTISEND_SELECTOR[2:]):
            actual_selector = "0x" + nested_data_hex[:8]
            return [], f"Nested call is not a multiSend. Actual selector: {actual_selector}"

        # Decode the multiSend(bytes) call
        multisend_data_bytes = nested_data_bytes[4:]
        packed_txs_bytes, = decode(['bytes'], multisend_data_bytes)

        # Loop through the tightly packed inner transactions
        forwarded_addresses = []
        cursor = 0
        while cursor < len(packed_txs_bytes):
            to_bytes = packed_txs_bytes[cursor + 1 : cursor + 21]
            data_len_bytes = packed_txs_bytes[cursor + 53 : cursor + 85]
            data_len = int.from_bytes(data_len_bytes, 'big')
            forwarded_addresses.append(to_checksum_address(to_bytes))
            cursor += (1 + 20 + 32 + 32 + data_len)
        
        # On success, return the list of addresses and None for the reason
        return forwarded_addresses, None

    except Exception as e:
        return [], f"A decoding error occurred: {e}"

def main():
    """Main function that now prints the reason for skipping."""
    print("--- Focused Decoder for execTransaction Calls ---")
    
    print(f"Reading transactions from {INPUT_CSV_PATH}...")
    df = pd.read_csv(INPUT_CSV_PATH)
    print("Decoding transactions...")
    
    decoded_records = []
    skipped_txs = []
    
    for _, row in df.iterrows():
        tx_hash = row['tx_hash']
        input_data = row['input']
        
        addresses, reason = decode_multisend_from_exec_tx(input_data)
        
        if addresses:
            for addr in addresses:
                decoded_records.append({
                    'tx_hash': tx_hash,
                    'forwarded_to_address': addr
                })
        else:
            skipped_txs.append({'hash': tx_hash, 'reason': reason})

    output_df = pd.DataFrame(decoded_records)
    if not output_df.empty:
        os.makedirs(os.path.dirname(OUTPUT_CSV_PATH), exist_ok=True)
        output_df.to_csv(OUTPUT_CSV_PATH, index=False)

    print(f"\n✅ Success! Decoding complete.")
    if not output_df.empty:
        print(f"   - Decoded {len(output_df)} forwarded addresses from multiSend calls.")
        print(f"   Results saved to {OUTPUT_CSV_PATH}")
    
    # --- CHANGE: Print the detailed reason for each skipped transaction ---
    if skipped_txs:
        print(f"\n   - Skipped {len(skipped_txs)} transaction(s) for the following reasons:")
        for skipped in skipped_txs:
            print(f"     - Hash: {skipped['hash']}")
            print(f"       Reason: {skipped['reason']}")

if __name__ == "__main__":
    main()