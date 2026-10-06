WITH source_summary AS (

    SELECT
        'paystack' AS data_source,
        COUNT(*) AS source_transaction_count,
        SUM(amount) / 100.0 AS source_amount_ngn
    FROM {{ source('paystack', 'paystack_transactions') }}

    UNION ALL

    SELECT
        'synthetic' AS data_source,
        COUNT(*) AS source_transaction_count,
        SUM(amount) / 100.0 AS source_amount_ngn
    FROM {{ source('synthetic', 'synthetic_transactions') }}

),

fact_summary AS (

    SELECT
        data_source,
        COUNT(*) AS fact_transaction_count,
        SUM(amount_ngn) AS fact_amount_ngn
    FROM {{ ref('fact_transactions') }}
    GROUP BY data_source

)

SELECT
    s.data_source,

    s.source_transaction_count,
    f.fact_transaction_count,

    s.source_amount_ngn,
    f.fact_amount_ngn,

    f.fact_transaction_count - s.source_transaction_count
        AS transaction_count_difference,

    f.fact_amount_ngn - s.source_amount_ngn
        AS amount_difference_ngn,

    CASE
        WHEN s.source_transaction_count = f.fact_transaction_count
         AND ABS(s.source_amount_ngn - f.fact_amount_ngn) < 0.01
        THEN 'RECONCILED'
        ELSE 'MISMATCH'
    END AS reconciliation_status

FROM source_summary s

LEFT JOIN fact_summary f
    ON s.data_source = f.data_source