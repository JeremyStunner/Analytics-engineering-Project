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
    is_successful,
    is_failed,
    is_unresolved,
    transaction_date
FROM {{ ref('int_transactions') }}