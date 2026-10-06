SELECT
    DATE(transaction_created_at) AS transaction_date,

    currency,

    payment_channel,

    data_source,

    COUNT(*) AS total_transactions,

    COUNT(*) FILTER (
        WHERE transaction_status = 'success'
    ) AS successful_transactions,

    COUNT(*) FILTER (
        WHERE transaction_status = 'failed'
    ) AS failed_transactions,

    COUNT(*) FILTER (
        WHERE transaction_status = 'abandoned'
    ) AS abandoned_transactions,

    COUNT(*) FILTER (
        WHERE transaction_status = 'pending'
    ) AS pending_transactions,

    SUM(amount_ngn) AS total_transaction_value_ngn,

    SUM(amount_ngn) FILTER (
        WHERE transaction_status = 'success'
    ) AS successful_transaction_value_ngn,

    ROUND(
        100.0 * COUNT(*) FILTER (
            WHERE transaction_status = 'success'
        ) / NULLIF(COUNT(*), 0),
        2
    ) AS success_rate

FROM {{ ref('fact_transactions') }}

GROUP BY
    DATE(transaction_created_at),
    currency,
    payment_channel,
    data_source