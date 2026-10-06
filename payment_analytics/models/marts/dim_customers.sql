SELECT
    customer_id,
    COUNT(*) AS total_transactions,
    SUM(amount_ngn) AS total_amount_ngn,
    COUNT(*) FILTER (
        WHERE transaction_status = 'success'
    ) AS successful_transactions,
    COUNT(*) FILTER (
        WHERE transaction_status = 'failed'
    ) AS failed_transactions,
    MIN(transaction_created_at) AS first_transaction_at,
    MAX(transaction_created_at) AS last_transaction_at
FROM {{ ref('stg_transactions') }}
WHERE customer_id IS NOT NULL
GROUP BY customer_id