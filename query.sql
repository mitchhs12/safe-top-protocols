WITH gnosis_safe_contracts (address) AS (
    VALUES
        -- MultiSend Contracts
        (0x40A2ACCBD92BCA938B02010E17A5B8929B49130D), -- MultiSendCallOnly v1.3.0
        (0x8D29BE29923B68ABFDD21E541B9374737B49CDAD), -- MultiSend v1.1.1
        (0xA238CBEB142C10EF7AD8442C6D1F9E89E07E7761), -- MultiSend v1.3.0
        (0x998739BF44842d75A7595475440447572A8B3C58), -- MultiSend v1.4.1
        (0x9641D764FC13C8B624C04430C7356C1C7C8102E2), -- MultiSendCallOnly v1.4.1
        (0xB522A9F781924ED250A11C54105E51840B138ADD), -- MultiSend v1.1.0
        (0x6851D6FDFAFD08C0295C392436245E5BC78B0185), -- Safe Mastercopy 1.2.0

        -- Safe Singleton / Implementation Contracts (L1 & L2)
        (0x3E5C63644E683549055B9BE8653DE26E0B4CD36E), -- GnosisSafeL2 v1.3.0
        (0xFB1BFFC9D739B8D520DAF37DF666DA4C687191EA), -- GnosisSafeL2 v1.3.0 + Fallback
        (0x41675C099F32341BF84BFC5382AF534DF5C7461A), -- Safe L2 v1.4.1
        (0x60EB332BD4A0E2A9EEB3212CFDD6EF03CE4CB3B5), -- GnosisSafeL2 v1.3.0 (via Proxy)
        
        -- Proxy Factory Contracts
        (0xD9DB270C1B5E3BD161E8C8503C55CEABEE709552), -- GnosisSafeProxyFactory v1.3.0
        (0x34CFAC646F301356FAA8B21E94227E3583FE3F5F), -- GnosisSafeProxyFactory v1.1.1
        
        -- Core Utility Libraries & Modules
        (0xA65387F16B013CF2AF4605AD8AA5EC25A2CBA3A2) -- SignMessageLib v1.3.0
),

-- Step 1: Decode the immediate destination from all successful Safe transactions
initial_decoded_txs AS (
    SELECT
        address AS safe_wallet,
        tx_hash,
        block_date,
        BYTEARRAY_SUBSTRING(input, 17, 20) AS destination_binary
    FROM safe_ethereum.transactions
    WHERE method = 'execTransaction' AND success = true AND BYTEARRAY_LENGTH(input) >= 36 AND input IS NOT NULL
),

-- Get all direct calls that DO NOT go to a Gnosis Safe contract.
-- These are counted as the final destination (regular transactions).
regular_transactions AS (
    SELECT
        safe_wallet,
        tx_hash,
        block_date,
        destination_binary
    FROM initial_decoded_txs
    WHERE destination_binary NOT IN (SELECT address FROM gnosis_safe_contracts)
)

-- Final Step: Aggregate the results for the final report
SELECT
    CONCAT('0x', TO_HEX(destination_binary)) AS destination_contract,
    COUNT(*) AS interaction_count,
    COUNT(DISTINCT safe_wallet) AS unique_safe_wallets,
    MIN(block_date) AS first_interaction_date,
    MAX(block_date) AS last_interaction_date
FROM regular_transactions
WHERE
    destination_binary IS NOT NULL
    AND destination_binary != 0x0000000000000000000000000000000000000000
GROUP BY 1
ORDER BY interaction_count DESC
LIMIT 100;