-- Step 1: Decode the immediate destination from all successful Safe transactions in the last 30 days
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
      AND block_date >= CURRENT_DATE - INTERVAL '30' DAY
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
LIMIT 100;
