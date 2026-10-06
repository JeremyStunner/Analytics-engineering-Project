SELECT
    transaction_id,
    transaction_reference,
    customer_id,
    transaction_status,
    amount_kobo,
    amount_ngn,
    currency,
    payment_channel,
    transaction_created_at,
    transaction_paid_at,
    ingested_at,
    data_source,

    CASE
        WHEN transaction_status = 'success' THEN 1
        ELSE 0
    END AS is_successful,

    CASE
        WHEN transaction_status = 'failed' THEN 1
        ELSE 0
    END AS is_failed,

    CASE
        WHEN transaction_status IN ('abandoned', 'pending') THEN 1
        ELSE 0
    END AS is_unresolved,

    DATE(transaction_created_at) AS transaction_date

FROM {{ ref('stg_transactions') }}