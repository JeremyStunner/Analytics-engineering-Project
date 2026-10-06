WITH source AS (

    SELECT *
    FROM {{ source('paystack', 'paystack_transactions') }}

),

cleaned AS (

    SELECT
        transaction_id,
        reference AS transaction_reference,
        LOWER(TRIM(status)) AS transaction_status,
        amount AS amount_kobo,
        amount / 100.0 AS amount_ngn,
        UPPER(TRIM(currency)) AS currency,
        LOWER(TRIM(channel)) AS payment_channel,
        customer_id,
        created_at AS transaction_created_at,
        paid_at AS transaction_paid_at,
        ingested_at

    FROM source

)

SELECT *
FROM cleaned