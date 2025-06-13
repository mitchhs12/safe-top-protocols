from eth_abi import encode as encode_abi
from eth_utils import to_checksum_address, keccak, to_bytes

# --- Function Selectors ---
EXEC_TX_SIGNATURE = 'execTransaction(address,uint256,bytes,uint8,uint256,uint256,uint256,address,address,bytes)'
MULTISEND_SIGNATURE = 'multiSend(bytes)'

EXEC_TX_SELECTOR = "0x" + keccak(text=EXEC_TX_SIGNATURE)[:4].hex()
MULTISEND_SELECTOR = "0x" + keccak(text=MULTISEND_SIGNATURE)[:4].hex() # Note: The Safe uses this canonical selector internally

# --- Helper function to pack a single inner transaction ---
def encode_single_transaction(to_address: str, value_in_wei: int = 0, data: bytes = b'') -> bytes:
    """
    Packs a single transaction for the multiSend call into a byte string.
    """
    # Operation type: 0 for a standard CALL
    op = to_bytes(0, size=1)
    
    # Address: Must be checksummed, then converted to 20 bytes
    to = to_bytes(hexstr=to_checksum_address(to_address))
    
    # Value: Encode as a 32-byte integer
    value = to_bytes(value_in_wei, size=32)
    
    # Data Length: The length of the data payload, as a 32-byte integer
    data_len = to_bytes(len(data), size=32)
    
    # Concatenate all parts
    return op + to + value + data_len + data

# --- Main Re-encoding Logic ---
def main():
    print("--- Re-encoding a Gnosis Safe multiSend Transaction ---")

    # --- 1. Define the Parameters for our Transaction ---
    # The address of the MultiSend library contract that the Safe will call
    multisend_contract_address = '0xA238CBeb142c10Ef7Ad8442C6D1f9E89e07e7761'
    
    # The list of addresses we want the multiSend call to forward funds to
    destination_addresses = [
        '0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B', # Vitalik Buterin
        '0x5aFE3855358E112B5647B952709E6165e1c1eEEe', # Gnosis Safe: Proxy Factory
        '0x000000000000000000000000000000000000dEaD'  # A burn address
    ]
    print(f"\n[Step 1] Defined parameters: 3 destinations, calling MultiSend at {multisend_contract_address[:10]}...")

    # --- 2. Encode the Innermost Data: The list of transactions ---
    packed_transactions = b''
    for addr in destination_addresses:
        packed_transactions += encode_single_transaction(addr)
    
    print(f"\n[Step 2] Created the packed bytes for the inner transactions.")
    print(f"   - Packed Bytes (snippet): 0x{packed_transactions.hex()[:60]}...")
    print(f"   - Total Length: {len(packed_transactions)} bytes")


    # --- 3. Create the `multiSend` function call payload ---
    # The multiSend function takes one 'bytes' argument. We must ABI-encode our packed_transactions.
    # The result is: (32-byte length header) + (the packed_transactions data)
    multisend_inner_payload = encode_abi(['bytes'], [packed_transactions])
    
    # Now, prepend the multiSend function selector
    multisend_full_payload = to_bytes(hexstr=MULTISEND_SELECTOR) + multisend_inner_payload
    
    print(f"\n[Step 3] Created the full payload for the nested `multiSend` call.")
    print(f"   - Full Payload (snippet): 0x{multisend_full_payload.hex()[:60]}...")


    # --- 4. Create the Outermost `execTransaction` call payload ---
    # We need to provide all arguments for the execTransaction function.
    # IMPORTANT: For a perfect match with a real transaction, these values (especially gas)
    # would need to be identical to the original. We use 0 for simplicity here.
    exec_tx_args = {
        'to': to_checksum_address(multisend_contract_address),
        'value': 0,
        'data': multisend_full_payload,
        'operation': 1, # 1 for DELEGATECALL, which is standard for multiSend
        'safeTxGas': 0,
        'baseGas': 0,
        'gasPrice': 0,
        'gasToken': '0x0000000000000000000000000000000000000000',
        'refundReceiver': '0x0000000000000000000000000000000000000000',
        'signatures': b''
    }

    # Define the ABI types for the function in the correct order
    exec_tx_abi_types = [
        'address', 'uint256', 'bytes', 'uint8', 'uint256', 
        'uint256', 'uint256', 'address', 'address', 'bytes'
    ]
    
    # Encode the arguments
    exec_tx_payload = encode_abi(exec_tx_abi_types, list(exec_tx_args.values()))

    # Prepend the execTransaction selector to get the final input data
    final_input_data = EXEC_TX_SELECTOR + exec_tx_payload.hex()
    
    print(f"\n[Step 4] Created the final `execTransaction` input data.")
    print(f"\n--- FINAL RESULT ---")
    print(f"Re-encoded Input Data:\n{final_input_data}")
    print("--------------------")
    print("\nThis hex string is the final 'input' data that would be sent to the Gnosis Safe contract.")
    print("You can now compare this generated string with an input from your CSV to verify the structure.")


if __name__ == "__main__":
    main()