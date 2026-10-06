import os
import requests
import psycopg2
from pathlib import Path
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from psycopg2.extras import Json


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("PAYSTACK_SECRET_KEY")

if not API_KEY or not API_KEY.startswith("sk_test_"):
    raise ValueError("Missing Paystack test secret key")


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "payment_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD")
    )


# ============================================================
# ETL LOGGING
# ============================================================

def start_ingestion_log():
    """Create a log entry when the pipeline starts."""

    conn = get_db_connection()

    try:
        with conn:
            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    INSERT INTO etl.ingestion_log (
                        pipeline_name,
                        started_at,
                        status
                    )
                    VALUES (%s, %s, %s)
                    RETURNING run_id;
                    """,
                    (
                        "paystack_transactions",
                        datetime.now(timezone.utc),
                        "RUNNING"
                    )
                )

                run_id = cursor.fetchone()[0]

        return run_id

    finally:
        conn.close()


def update_ingestion_log(
    run_id,
    records_processed,
    status,
    error_message=None
):
    """Update the pipeline log when processing finishes."""

    conn = get_db_connection()

    try:
        with conn:
            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    UPDATE etl.ingestion_log
                    SET
                        completed_at = %s,
                        records_processed = %s,
                        status = %s,
                        error_message = %s
                    WHERE run_id = %s;
                    """,
                    (
                        datetime.now(timezone.utc),
                        records_processed,
                        status,
                        error_message,
                        run_id
                    )
                )

    finally:
        conn.close()


# ============================================================
# EXTRACT
# ============================================================

def get_latest_transaction_timestamp():
    """
    Get the latest transaction timestamp already stored
    in PostgreSQL.
    """

    conn = get_db_connection()

    try:
        with conn:
            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    SELECT MAX(created_at)
                    FROM raw.paystack_transactions;
                    """
                )

                result = cursor.fetchone()

                return result[0]

    finally:
        conn.close()


def extract_transactions():
    """
    Fetch recent Paystack transactions using a
    5-minute lookback window.
    """

    transactions = []

    page = 1

    latest_created_at = get_latest_transaction_timestamp()

    # --------------------------------------------------------
    # Determine extraction window
    # --------------------------------------------------------

    if latest_created_at:

        start_date = latest_created_at - timedelta(minutes=5)

        print(
            f"Latest transaction in database: "
            f"{latest_created_at}"
        )

        print(
            f"Incremental extraction starting from: "
            f"{start_date}"
        )

    else:

        start_date = None

        print(
            "No existing transactions found."
        )

        print(
            "Performing initial extraction."
        )

    # --------------------------------------------------------
    # Call Paystack API
    # --------------------------------------------------------

    with requests.Session() as session:

        session.headers.update({
            "Authorization": f"Bearer {API_KEY}"
        })

        while True:

            params = {
                "page": page,
                "perPage": 50
            }

            # Paystack API supports filtering transactions
            # using a start date.
            if start_date:

                params["from"] = start_date.strftime(
                    "%Y-%m-%dT%H:%M:%S.000Z"
                )

            response = session.get(
                "https://api.paystack.co/transaction",
                params=params,
                timeout=30
            )

            response.raise_for_status()

            result = response.json()

            if not result.get("status"):
                raise RuntimeError(
                    result.get("message")
                )

            records = result.get("data", [])

            transactions.extend(records)

            print(
                f"Page {page}: "
                f"{len(records)} records"
            )

            # Stop when fewer than 50 records
            # are returned.
            if len(records) < 50:
                break

            page += 1

    return transactions


# ============================================================
# LOAD
# ============================================================

def load_transactions(transactions):
    """
    Load transactions into PostgreSQL using upserts.
    """

    sql = """
        INSERT INTO raw.paystack_transactions (
            transaction_id,
            reference,
            status,
            amount,
            currency,
            channel,
            customer_id,
            created_at,
            paid_at,
            raw_payload
        )
        VALUES (
            %(transaction_id)s,
            %(reference)s,
            %(status)s,
            %(amount)s,
            %(currency)s,
            %(channel)s,
            %(customer_id)s,
            %(created_at)s,
            %(paid_at)s,
            %(raw_payload)s
        )

        ON CONFLICT (transaction_id)
        DO UPDATE SET
            reference = EXCLUDED.reference,
            status = EXCLUDED.status,
            amount = EXCLUDED.amount,
            currency = EXCLUDED.currency,
            channel = EXCLUDED.channel,
            customer_id = EXCLUDED.customer_id,
            created_at = EXCLUDED.created_at,
            paid_at = EXCLUDED.paid_at,
            raw_payload = EXCLUDED.raw_payload,
            ingested_at = NOW()
    """

    conn = get_db_connection()

    try:

        with conn:

            with conn.cursor() as cursor:

                for tx in transactions:

                    customer = tx.get("customer") or {}

                    cursor.execute(
                        sql,
                        {
                            "transaction_id": tx["id"],

                            "reference": tx.get(
                                "reference"
                            ),

                            "status": tx.get(
                                "status"
                            ),

                            "amount": tx.get(
                                "amount"
                            ),

                            "currency": tx.get(
                                "currency"
                            ),

                            "channel": tx.get(
                                "channel"
                            ),

                            "customer_id": (
                                customer.get("id")
                                if isinstance(
                                    customer,
                                    dict
                                )
                                else None
                            ),

                            "created_at": tx.get(
                                "created_at"
                            ),

                            "paid_at": tx.get(
                                "paid_at"
                            ),

                            "raw_payload": Json(tx)
                        }
                    )

    finally:

        conn.close()


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    run_id = start_ingestion_log()

    print(
        f"Pipeline run ID: {run_id}"
    )

    try:

        # -----------------------------
        # Extract
        # -----------------------------

        transactions = extract_transactions()

        # -----------------------------
        # Load
        # -----------------------------

        if transactions:

            load_transactions(
                transactions
            )

        # -----------------------------
        # Success
        # -----------------------------

        print(
            f"Successfully processed "
            f"{len(transactions)} transactions."
        )

        update_ingestion_log(
            run_id=run_id,
            records_processed=len(
                transactions
            ),
            status="SUCCESS"
        )

        print(
            "Pipeline status: SUCCESS"
        )

    except Exception as e:

        # -----------------------------
        # Failure
        # -----------------------------

        update_ingestion_log(
            run_id=run_id,
            records_processed=0,
            status="FAILED",
            error_message=str(e)
        )

        print(
            "Pipeline status: FAILED"
        )

        print(
            f"Error: {e}"
        )

        raise


# ============================================================
# RUN PIPELINE
# ============================================================

if __name__ == "__main__":
    main()