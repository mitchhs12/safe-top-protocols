from eth_utils import to_checksum_address
import binascii

def analyze_multisend_encoding(data_hex_string: str):
    """Analyzes and visualizes the encoding structure of a multiSend payload."""
    print("=" * 80)
    print("MULTISEND DATA PAYLOAD ANALYSIS")
    print("=" * 80)
    
    # Ensure the hex string has the '0x' prefix
    if not data_hex_string.startswith('0x'):
        data_hex_string = '0x' + data_hex_string

    data_bytes = bytes.fromhex(data_hex_string[2:])
    
    print(f"📊 Total payload length: {len(data_bytes)} bytes ({len(data_hex_string)} hex chars)")
    print(f"📊 Raw hex data: {data_hex_string}")
    print()
    
    # 1. Function selector (first 4 bytes)
    selector = data_bytes[:4]
    print(f"🔍 FUNCTION SELECTOR (bytes 0-3):")
    print(f"   Hex: {selector.hex()}")
    print(f"   Expected: 8d80ff0a (multiSend)")
    print(f"   Match: {'✅' if selector.hex() == '8d80ff0a' else '❌'}")
    print()
    
    if selector.hex() != '8d80ff0a':
        print("❌ Not a multiSend transaction!")
        return
    
    # 2. Function parameters (after selector)
    func_params = data_bytes[4:]
    print(f"🔍 FUNCTION PARAMETERS (bytes 4+):")
    print(f"   Length: {len(func_params)} bytes")
    print()
    
    # 3. Offset to dynamic data (first 32 bytes of parameters)
    offset_bytes = func_params[:32]
    offset = int.from_bytes(offset_bytes, 'big')
    print(f"🔍 OFFSET TO DYNAMIC DATA (bytes 4-35):")
    print(f"   Hex: {offset_bytes.hex()}")
    print(f"   Decimal: {offset}")
    print(f"   Points to byte: {4 + offset} (from start of payload)")
    print()
    
    # 4. Length of packed transactions (at offset position)
    length_start = offset
    length_bytes = func_params[length_start:length_start + 32]
    length = int.from_bytes(length_bytes, 'big')
    print(f"🔍 LENGTH OF PACKED TRANSACTIONS (bytes {4 + length_start}-{4 + length_start + 31}):")
    print(f"   Hex: {length_bytes.hex()}")
    print(f"   Decimal: {length}")
    print()
    
    # 5. Packed transactions data
    txs_start = length_start + 32
    txs_end = txs_start + length
    packed_txs_bytes = func_params[txs_start:txs_end]
    print(f"🔍 PACKED TRANSACTIONS DATA (bytes {4 + txs_start}-{4 + txs_end - 1}):")
    print(f"   Length: {len(packed_txs_bytes)} bytes")
    print(f"   Hex: {packed_txs_bytes.hex()}")
    print()
    
    # 6. Parse individual transactions
    print("🔍 INDIVIDUAL TRANSACTIONS BREAKDOWN:")
    print("   Format: [operation(1)] [to(20)] [value(32)] [dataLength(32)] [data(?)]")
    print()
    
    cursor = 0
    tx_num = 1
    
    while cursor < len(packed_txs_bytes):
        try:
            print(f"   📋 Transaction #{tx_num}:")
            
            # Operation (1 byte)
            if cursor >= len(packed_txs_bytes):
                break
            operation = packed_txs_bytes[cursor]
            print(f"      Operation (byte {cursor}): {operation} ({'CALL' if operation == 0 else 'DELEGATECALL' if operation == 1 else 'UNKNOWN'})")
            
            # To address (20 bytes)
            to_start = cursor + 1
            to_end = to_start + 20
            if to_end > len(packed_txs_bytes):
                print(f"      ❌ Incomplete transaction data")
                break
            to_bytes = packed_txs_bytes[to_start:to_end]
            to_address = to_checksum_address(to_bytes)
            print(f"      To address (bytes {to_start}-{to_end-1}): {to_address}")
            
            # Value (32 bytes)
            value_start = to_end
            value_end = value_start + 32
            if value_end > len(packed_txs_bytes):
                print(f"      ❌ Incomplete transaction data")
                break
            value_bytes = packed_txs_bytes[value_start:value_end]
            value = int.from_bytes(value_bytes, 'big')
            print(f"      Value (bytes {value_start}-{value_end-1}): {value} wei")
            
            # Data length (32 bytes)
            data_len_start = value_end
            data_len_end = data_len_start + 32
            if data_len_end > len(packed_txs_bytes):
                print(f"      ❌ Incomplete transaction data")
                break
            data_len_bytes = packed_txs_bytes[data_len_start:data_len_end]
            data_len = int.from_bytes(data_len_bytes, 'big')
            print(f"      Data length (bytes {data_len_start}-{data_len_end-1}): {data_len} bytes")
            
            # Data payload
            data_start = data_len_end
            data_end = data_start + data_len
            if data_end > len(packed_txs_bytes):
                print(f"      ❌ Incomplete transaction data")
                break
            data_payload = packed_txs_bytes[data_start:data_end]
            print(f"      Data payload (bytes {data_start}-{data_end-1}):")
            print(f"         Hex: {data_payload.hex()}")
            
            # Try to decode function selector if data exists
            if len(data_payload) >= 4:
                func_selector = data_payload[:4].hex()
                print(f"         Function selector: {func_selector}")
                
                # Common function selectors
                selectors = {
                    '1e83409a': 'setModule(address,bool)',
                    'b460af94': 'swapTokensForExactTokens(...)',
                    '095ea7b3': 'approve(address,uint256)',
                    'c73a2d60': 'distributeToken(address,address[],uint256[])'
                }
                if func_selector in selectors:
                    print(f"         Function: {selectors[func_selector]}")
            
            cursor = data_end
            tx_num += 1
            print()
            
        except Exception as e:
            print(f"      ❌ Error parsing transaction: {e}")
            break
    
    print(f"✅ Successfully parsed {tx_num - 1} transactions")

if __name__ == "__main__":
    # Test with your data
    data_payload = "0x8d80ff0a000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000003fd00048626055cbbbd60362247069cae610c62c5b903000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000241e83409a000000000000000000000000bd5ca40c66226f53378ae06bc71784cad6016087005275876129bc75db7b523d3045951369efde4ad0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000241e83409a000000000000000000000000bd5ca40c66226f53378ae06bc71784cad601608700be53a109b494e5c9f97b9cd39fe969be68bf620400000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000064b460af940000000000000000000000000000000000000000000000000000000735e57040000000000000000000000000bd5ca40c66226f53378ae06bc71784cad6016087000000000000000000000000bd5ca40c66226f53378ae06bc71784cad601608700a0b86991c6218b36c1d19d4a2e9eb0ce3606eb4800000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000044095ea7b3000000000000000000000000d152f549545093347a162dce210e7293f14521500000000000000000000000000000000000000000000000000000000735e5704000d152f549545093347a162dce210e7293f145215000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000164c73a2d60000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb48000000000000000000000000000000000000000000000000000000000000006000000000000000000000000000000000000000000000000000000000000000e0000000000000000000000000000000000000000000000000000000000000000300000000000000000000000015d7d53f578bafe720761e83bcc42a23de79f4d9000000000000000000000000fed8555bde8def739bec596a1b6309185c4096f5000000000000000000000000edc25d698d899b261f8cecedddc23ac50ff4f419000000000000000000000000000000000000000000000000000000000000000300000000000000000000000000000000000000000000000000000004dd684f7000000000000000000000000000000000000000000000000000000001e1478cd00000000000000000000000000000000000000000000000000000000077359400000000"
    analyze_multisend_encoding(data_payload)