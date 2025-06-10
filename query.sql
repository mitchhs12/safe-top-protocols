-- This query is used to retrieve the top 100 most frequently called contracts from Safe wallets.
-- It does this by drilling down into any transaction that interacts with the Gnosis/Safe infrastructure contracts.
-- It then aggregates the results to get the top 100 most frequently called contracts.
-- Note: I did not filter all gnosis multisend contracts, just the ones that were used in the top 100.

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
        (0xA65387F16B013CF2AF4605AD8AA5EC25A2CBA3A2), -- SignMessageLib v1.3.0
        (0x8629BCD3B8A90FD7247F0C0E0E1434C69DADCCA7), -- Create2ForwarderFactory (from Zodiac)
        (0x87870BCA3F3FD6335C3F4CE8392D69350B4FA4E2)  -- Zodiac Delay Module (Proxy)
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

-- Step 2 (Branch A): Get all direct calls that DO NOT go to a Gnosis Safe contract.
-- These are counted as the final destination.
direct_interactions AS (
    SELECT
        safe_wallet,
        tx_hash,
        block_date,
        destination_binary
    FROM initial_decoded_txs
    WHERE destination_binary NOT IN (SELECT address FROM gnosis_safe_contracts)
),

-- Step 3: Identify the parent transactions that DID call a Gnosis Safe contract.
gnosis_call_parent_txs AS (
    SELECT
        tx_hash,
        safe_wallet
    FROM initial_decoded_txs
    WHERE destination_binary IN (SELECT address FROM gnosis_safe_contracts)
),

-- Step 4 (Branch B): For the Gnosis-related transactions, find all successful internal calls they triggered.
unpacked_interactions AS (
    SELECT
        p.safe_wallet,
        t.tx_hash,
        t.block_date,
        t.to AS destination_binary -- The 'to' of the internal call is the true destination.
    FROM safe_ethereum.transactions AS t
    JOIN gnosis_call_parent_txs AS p ON t.tx_hash = p.tx_hash
    WHERE t.success = true AND t.to IS NOT NULL AND t.to NOT IN (SELECT address FROM gnosis_safe_contracts)
),

-- Step 5: Combine the direct calls and the unpacked calls
all_final_interactions AS (
    SELECT * FROM direct_interactions
    UNION ALL
    SELECT * FROM unpacked_interactions
)

-- Final Step: Aggregate the results for the final report
SELECT
    CONCAT('0x', TO_HEX(destination_binary)) AS destination_contract,
    COUNT(*) AS interaction_count,
    COUNT(DISTINCT safe_wallet) AS unique_safe_wallets,
    MIN(block_date) AS first_interaction_date,
    MAX(block_date) AS last_interaction_date
FROM all_final_interactions
WHERE
    destination_binary IS NOT NULL
    AND destination_binary != 0x0000000000000000000000000000000000000000
GROUP BY 1
ORDER BY interaction_count DESC
LIMIT 100;