import os
import pandas as pd
from eth_abi import decode, encode as encode_abi
from eth_utils import to_checksum_address, keccak

# --- Configuration ---
INPUT_CSV_PATH = '../data/multisend_transactions.csv'

# --- The Full execTransaction ABI Definition ---
EXEC_TX_SIGNATURE = 'execTransaction(address,uint256,bytes,uint8,uint256,uint256,uint256,address,address,bytes)'
EXEC_TX_SELECTOR = "0x" + keccak(text=EXEC_TX_SIGNATURE)[:4].hex()

EXEC_TX_ABI_TYPES = [
    'address', 'uint256', 'bytes', 'uint8', 'uint256',
    'uint256', 'uint256', 'address', 'address', 'bytes'
]

EXEC_TX_PARAM_NAMES = [
    'To', 'Value', 'Data', 'Operation', 'Safe Tx Gas',
    'Base Gas', 'Gas Price', 'Gas Token', 'Refund Receiver', 'Signatures'
]

# --- Nested multiSend helpers ---
MULTISEND_SELECTOR_IN_PAYLOAD = "0x8d80ff0a"

def parse_packed_transactions(packed_txs_bytes: bytes) -> list[str]:
    """Manually parses the tightly-packed data from a multiSend call."""
    addresses = []
    cursor = 0
    while cursor < len(packed_txs_bytes):
        try:
            to_bytes = packed_txs_bytes[cursor + 1 : cursor + 21]
            data_len_bytes = packed_txs_bytes[cursor + 53 : cursor + 85]
            data_len = int.from_bytes(data_len_bytes, 'big')
            addresses.append(to_checksum_address(to_bytes))
            cursor += (1 + 20 + 32 + 32 + data_len)
        except Exception:
            break
    return addresses

def decode_nested_multisend_payload(nested_data_bytes: bytes):
    """Decodes the `data` payload if it's a multiSend call."""
    nested_data_hex = nested_data_bytes.hex()
    if not nested_data_hex.startswith(MULTISEND_SELECTOR_IN_PAYLOAD[2:]):
        print(f"      Note: Nested call is not a multiSend. Selector is 0x{nested_data_hex[:8]}")
        return

    print("      --- Nested multiSend Call Details ---")
    try:
        multisend_func_payload = nested_data_bytes[4:]
        offset = int.from_bytes(multisend_func_payload[0:32], 'big')
        length = int.from_bytes(multisend_func_payload[offset : offset + 32], 'big')
        start_of_txs = offset + 32
        end_of_txs = start_of_txs + length
        actual_txs_bytes = multisend_func_payload[start_of_txs:end_of_txs]
        
        forwarded_addresses = parse_packed_transactions(actual_txs_bytes)
        
        print(f"      Forwarded To ({len(forwarded_addresses)} addresses):")
        for i, addr in enumerate(forwarded_addresses, 1):
            print(f"        {i}. {addr}")
        print("      ------------------------------------")

    except Exception as e:
        print(f"      Could not decode nested multiSend: {e}")


def main():
    """Reads the first transaction, decodes it, then re-encodes it for verification."""
    print("--- Full Gnosis Safe execTransaction Decoder & Re-encoder ---")
    
    # 1. Read Data
    try:
        df = pd.read_csv(INPUT_CSV_PATH)
        first_tx_row = df.iloc[0]
        tx_hash = first_tx_row['tx_hash']
        original_input_data = first_tx_row['input']
        print(f"\nFound transaction to process: {tx_hash}")
    except Exception as e:
        print(f"❌ ERROR: Could not read the CSV file. {e}")
        return

    # 2. Decode the transaction
    if not isinstance(original_input_data, str) or not original_input_data.startswith(EXEC_TX_SELECTOR):
        print("❌ ERROR: The 'input' data is not a valid execTransaction call.")
        return
        
    data_payload_bytes = bytes.fromhex(original_input_data[10:])

    try:
        decoded_params = decode(EXEC_TX_ABI_TYPES, data_payload_bytes)
    except Exception as e:
        print(f"❌ An error occurred during decoding: {e}")
        return

    # 3. Print the decoded results
    print("\n--- Decoded execTransaction Parameters ---")
    for name, value in zip(EXEC_TX_PARAM_NAMES, decoded_params):
        if isinstance(value, bytes):
            formatted_value = f"0x{value.hex()}"
        elif isinstance(value, int) and name == 'Operation':
            op_type = "CALL" if value == 0 else "DELEGATE_CALL"
            formatted_value = f"{value} ({op_type})"
        elif isinstance(value, str):
            formatted_value = to_checksum_address(value)
        else:
            formatted_value = value
        print(f"  - {name+':':<20} {formatted_value}")
    print("----------------------------------------")

    # --- 4. NEW: Re-encode the parameters and verify ---
    print("\n--- Re-encoding Parameters for Verification ---")
    try:
        # Use the decoded parameters to build the payload back up
        reencoded_payload_bytes = encode_abi(EXEC_TX_ABI_TYPES, decoded_params)
        
        # Prepend the selector to create the full input string
        reencoded_input_data = EXEC_TX_SELECTOR + reencoded_payload_bytes.hex()
        
        print(f"  - Re-encoded Input:")
        print(f"    {reencoded_input_data}")
        
        # Compare the result with the original
        if reencoded_input_data.lower() == original_input_data.lower():
            print("\n✅ Success: Re-encoded data perfectly matches the original input!")
        else:
            print("\n❌ Mismatch: Re-encoded data does NOT match the original input.")
            
    except Exception as e:
        print(f"❌ An error occurred during re-encoding: {e}")
    print("---------------------------------------------")

    # 5. Decode the nested payload for full context
    nested_payload = decoded_params[2]
    decode_nested_multisend_payload(nested_payload)


if __name__ == "__main__":
    main()