-- Step 1: Decode the immediate destination from all successful Safe transactions from the last 30 days, EXCLUDING multisend contracts
WITH initial_decoded_txs AS (
    SELECT
        address AS safe_wallet,
        tx_hash,
        block_date,
        BYTEARRAY_SUBSTRING(input, 17, 20) AS destination_binary
    FROM safe_ethereum.transactions
    WHERE method = 'execTransaction' 
      AND success = true 
      AND BYTEARRAY_LENGTH(input) >= 36 
      AND input IS NOT NULL
      AND block_time >= NOW() - INTERVAL '30' DAY

      -- This new condition excludes the specified multisend contracts --
      AND BYTEARRAY_SUBSTRING(input, 17, 20) NOT IN (
        from_hex(SUBSTR('0x8D29bE29923b68abfDD21e541b9374737B49cdAD', 3)), -- v1.1.1
        from_hex(SUBSTR('0xA238CBeb142c10Ef7Ad8442C6D1f9E89e07e7761', 3)), -- v1.3.0
        from_hex(SUBSTR('0x40A2aCCbd92BCA938b02010E17A5b8929b49130D', 3)), -- v1.3.0 multisend callonly
        from_hex(SUBSTR('0x38869bf66a61cF6bDB996A6aE40D5853Fd43B526', 3)), -- v1.4.1
        from_hex(SUBSTR('0x9641d764fc13c8B624c04430C7356C1C7C8102e2', 3))  -- v1.4.1 multisend callonly
    )
)

-- Final Step: Aggregate the results for the final report
SELECT
    CONCAT('0x', TO_HEX(destination_binary)) AS destination_contract,
    COUNT(*) AS interaction_count,
    COUNT(DISTINCT safe_wallet) AS unique_safe_wallets,
    MIN(block_date) AS first_interaction_date,
    MAX(block_date) AS last_interaction_date
FROM initial_decoded_txs
WHERE
    destination_binary IS NOT NULL
    AND destination_binary != 0x0000000000000000000000000000000000000000
GROUP BY 1
ORDER BY interaction_count DESC