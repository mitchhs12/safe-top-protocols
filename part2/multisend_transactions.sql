SELECT
    *
FROM
    safe_ethereum.transactions
WHERE
    -- We are only interested in successful execTransaction calls
    method = 'execTransaction' 
    AND success = true 
    AND BYTEARRAY_LENGTH(input) >= 36 -- Ensures the input data is long enough to contain an address
    
    -- This is the key filtering condition
    AND BYTEARRAY_SUBSTRING(input, 17, 20) IN (
        from_hex(SUBSTR('0x8D29bE29923b68abfDD21e541b9374737B49cdAD', 3)), -- v1.1.1
        from_hex(SUBSTR('0xA238CBeb142c10Ef7Ad8442C6D1f9E89e07e7761', 3)), -- v1.3.0
        from_hex(SUBSTR('0x40A2aCCbd92BCA938b02010E17A5b8929b49130D', 3)), -- v1.3.0 multisend callonly
        from_hex(SUBSTR('0x38869bf66a61cF6bDB996A6aE40D5853Fd43B526', 3)), -- v1.4.1
        from_hex(SUBSTR('0x9641d764fc13c8B624c04430C7356C1C7C8102e2', 3))  -- v1.4.1 multisend callonly
    )
AND block_time >= NOW() - INTERVAL '30' DAY
