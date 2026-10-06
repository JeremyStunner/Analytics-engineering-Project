import os
import random
from pathlib import Path
from datetime import datetime, timedelta, timezone

import psycopg2
from psycopg2.extras import Json
from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


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
# GENERATE TRANSACTIONS
# ============================================================

def generate_transactions(number_of_transactions=100):

    transactions = []

    statuses = [
        "success",
        "success",
        "success",
        "success",
        "success",
        "success",
        "success",
        "failed",
        "failed",
        "abandoned",
        "pending"
    ]

    channels = [
        "card",
        "bank",
        "ussd",
        "bank_transfer"
    ]

    amounts = [
        100000,      # ₦1,000
        150000,      # ₦1,500
        200000,      # ₦2,000
        250000,      # ₦2,500
        500000,      # ₦5,000
        750000,      # ₦7,500
        1000000,     # ₦10,000
        1500000,     # ₦15,000
        2500000,     # ₦25,000
        5000000,     # ₦50,000
        10000000     # ₦100,000
    ]

    now = datetime.now(timezone.utc)

    # Generate transactions across approximately 3 months
    start_date = now - timedelta(days=90)

    for i in range(number_of_transactions):

        transaction_id = 9000000000 + i

        reference = f"SYNTH_{transaction_id}"

        status = random.choice(statuses)

        amount = random.choice(amounts)

        channel = random.choice(channels)

        customer_id = random.randint(
            500000000,
            500000050
        )

        random_seconds = random.randint(
            0,
            int((now - start_date).total_seconds())
        )

        created_at = (
            start_date +
            timedelta(seconds=random_seconds)
        )

        # Only successful transactions receive paid_at
        if status == "success":

            paid_at = created_at + timedelta(
                seconds=random.randint(10, 180)
            )

        else:

            paid_at = None

        raw_payload = {
            "id": transaction_id,
            "reference": reference,
            "status": status,
            "amount": amount,
            "currency": "NGN",
            "channel": channel,
            "customer": {
                "id": customer_id
            },
            "created_at": created_at.isoformat(),
            "paid_at": (
                paid_at.isoformat()
                if paid_at
                else None
            ),
            "source": "synthetic_test_data"
        }

        transactions.append({
            "transaction_id": transaction_id,
            "reference": reference,
            "status": status,
            "amount": amount,
            "currency": "NGN",
            "channel": channel,
            "customer_id": customer_id,
            "created_at": created_at,
            "paid_at": paid_at,
            "raw_payload": raw_payload
        })

    return transactions


# ============================================================
# LOAD DATA
# ============================================================

def load_transactions(transactions):

    sql = """
        INSERT INTO raw.synthetic_transactions (
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
        DO NOTHING;
    """

    conn = get_db_connection()

    try:

        with conn:

            with conn.cursor() as cursor:

                for transaction in transactions:

                    # Convert Python dictionary to PostgreSQL JSONB
                    transaction_data = {
                        **transaction,
                        "raw_payload": Json(
                            transaction["raw_payload"]
                        )
                    }

                    cursor.execute(
                        sql,
                        transaction_data
                    )

    finally:

        conn.close()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print(
        "Generating synthetic payment transactions..."
    )

    transactions = generate_transactions(100)

    load_transactions(transactions)

    print(
        f"Successfully generated and loaded "
        f"{len(transactions)} synthetic transactions."
    )