from eth_utils import to_checksum_address

# --- Helper functions from the previous script ---

def parse_packed_transactions(packed_txs_bytes: bytes) -> list[str]:
    """Manually parses the tightly-packed data from a multiSend call."""
    addresses = []
    cursor = 0
    while cursor < len(packed_txs_bytes):
        try:
            # Each inner transaction: operation (1) + to (20) + value (32) + dataLength (32) + data
            to_bytes = packed_txs_bytes[cursor + 1 : cursor + 21]
            data_len_bytes = packed_txs_bytes[cursor + 53 : cursor + 85]
            data_len = int.from_bytes(data_len_bytes, 'big')
            addresses.append(to_checksum_address(to_bytes))
            cursor += (1 + 20 + 32 + 32 + data_len)
        except Exception:
            break
    return addresses

def decode_multisend_data(data_hex_string: str):
    """Decodes the provided data payload hex string."""
    print("--- Decoding Nested multiSend Payload ---")
    
    # Ensure the hex string has the '0x' prefix
    if not data_hex_string.startswith('0x'):
        data_hex_string = '0x' + data_hex_string

    nested_data_bytes = bytes.fromhex(data_hex_string[2:])
    nested_data_hex = nested_data_bytes.hex()
    
    if not nested_data_hex.startswith("8d80ff0a"):
        print(f"Error: Data does not start with the multiSend selector (0x8d80ff0a).")
        return
        
    try:
        # The payload for the multiSend function call (after the selector)
        multisend_func_payload = nested_data_bytes[4:]

        # The first 32 bytes is the OFFSET to the dynamic data.
        offset = int.from_bytes(multisend_func_payload[0:32], 'big')

        # At that offset, the first 32 bytes is the LENGTH of the data.
        length = int.from_bytes(multisend_func_payload[offset : offset + 32], 'big')

        # The actual packed transactions start after the length header.
        start_of_txs = offset + 32
        end_of_txs = start_of_txs + length
        actual_txs_bytes = multisend_func_payload[start_of_txs:end_of_txs]
        
        # Parse the extracted transaction bytes
        forwarded_addresses = parse_packed_transactions(actual_txs_bytes)
        
        print(f"\n✅ Success! Decoded {len(forwarded_addresses)} forwarded addresses:")
        for i, addr in enumerate(forwarded_addresses, 1):
            print(f"  {i}. {addr}")

    except Exception as e:
        print(f"❌ Could not decode nested multiSend: {e}")


# --- Main execution ---
if __name__ == "__main__":
    # Paste the full 'Data' payload from your previous output here
    data_payload_to_decode = "0x8d80ff0a000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000003fd00048626055cbbbd60362247069cae610c62c5b903000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000241e83409a000000000000000000000000bd5ca40c66226f53378ae06bc71784cad6016087005275876129bc75db7b523d3045951369efde4ad0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000241e83409a000000000000000000000000bd5ca40c66226f53378ae06bc71784cad601608700be53a109b494e5c9f97b9cd39fe969be68bf620400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064b460af940000000000000000000000000000000000000000000000000000000735e57040000000000000000000000000bd5ca40c66226f53378ae06bc71784cad6016087000000000000000000000000bd5ca40c66226f53378ae06bc71784cad601608700a0b86991c6218b36c1d19d4a2e9eb0ce3606eb4800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000d152f549545093347a162dce210e7293f14521500000000000000000000000000000000000000000000000000000000735e5704000d152f549545093347a162dce210e7293f145215000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000164c73a2d60000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb48000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000e0000000000000000000000000000000000000000000000000000000000000000300000000000000000000000015d7d53f578bafe720761e83bcc42a23de79f4d9000000000000000000000000fed8555bde8def739bec596a1b6309185c4096f5000000000000000000000000edc25d698d899b261f8cecedddc23ac50ff4f419000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000004dd684f7000000000000000000000000000000000000000000000000000000001e1478cd00000000000000000000000000000000000000000000000000000000077359400000000"
    
    decode_multisend_data(data_payload_to_decode)