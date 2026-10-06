SELECT
    data_source,
    source_transaction_count,
    fact_transaction_count,
    source_amount_ngn,
    fact_amount_ngn,
    transaction_count_difference,
    amount_difference_ngn,
    reconciliation_status
FROM {{ ref('mart_reconciliation') }}
WHERE reconciliation_status != 'RECONCILED'