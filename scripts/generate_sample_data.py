"""
Sample data generator for payment transactions and reference datasets.
Generates both good quality and bad quality batches for demo purposes.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os


# Ensure output directory exists
os.makedirs("sample_data", exist_ok=True)


def generate_bin_reference():
    """Generate BIN reference data."""
    bins = [
        ("411111", "Visa", "US"),
        ("424242", "Visa", "GB"),
        ("512345", "Mastercard", "CA"),
        ("543210", "Mastercard", "AU"),
        ("378282", "Amex", "US"),
        ("371449", "Amex", "GB"),
        ("601111", "Discover", "US"),
        ("352812", "JCB", "JP"),
        ("400000", "Visa", "DE"),
        ("520000", "Mastercard", "FR"),
    ]
    
    df = pd.DataFrame(bins, columns=["bin", "network", "issuer_country"])
    df.to_csv("sample_data/bin_reference.csv", index=False)
    print(f"✓ Generated bin_reference.csv ({len(df)} rows)")


def generate_currency_rules():
    """Generate currency decimal rules."""
    rules = [
        ("USD", 2),
        ("EUR", 2),
        ("GBP", 2),
        ("JPY", 0),
        ("CNY", 2),
        ("AUD", 2),
        ("CAD", 2),
        ("CHF", 2),
        ("HKD", 2),
        ("SGD", 2),
    ]
    
    df = pd.DataFrame(rules, columns=["currency", "decimal_places"])
    df.to_csv("sample_data/currency_rules.csv", index=False)
    print(f"✓ Generated currency_rules.csv ({len(df)} rows)")


def generate_mcc_codes():
    """Generate valid MCC codes."""
    mccs = [
        ("5411", "Grocery Stores"),
        ("5812", "Eating Places/Restaurants"),
        ("5999", "Miscellaneous Retail"),
        ("7011", "Hotels/Motels"),
        ("4111", "Local/Suburban Transit"),
        ("5541", "Service Stations"),
        ("5311", "Department Stores"),
        ("5912", "Drug Stores"),
        ("5814", "Fast Food Restaurants"),
        ("7230", "Beauty/Barber Shops"),
    ]
    
    df = pd.DataFrame(mccs, columns=["mcc", "description"])
    df.to_csv("sample_data/mcc_codes.csv", index=False)
    print(f"✓ Generated mcc_codes.csv ({len(df)} rows)")


def generate_transactions_batch1(n=1000):
    """Generate good quality transactions batch."""
    np.random.seed(42)
    random.seed(42)
    
    # Generate transaction IDs
    txn_ids = [f"TXN{str(i).zfill(8)}" for i in range(1, n+1)]
    
    # Generate timestamps
    base_time = datetime.now() - timedelta(hours=2)
    event_times = [base_time + timedelta(seconds=random.randint(0, 7200)) for _ in range(n)]
    settlement_times = [et + timedelta(hours=random.randint(1, 24)) for et in event_times]
    
    # Generate amounts
    amounts = np.random.lognormal(3, 1.5, n).round(2)
    amounts = np.clip(amounts, 1, 10000)
    
    # Generate currencies
    currencies = np.random.choice(["USD", "EUR", "GBP", "JPY", "CAD"], n, p=[0.5, 0.2, 0.15, 0.1, 0.05])
    
    # Adjust JPY amounts (no decimals)
    for i, curr in enumerate(currencies):
        if curr == "JPY":
            amounts[i] = round(amounts[i] * 100)
    
    # Generate other fields
    statuses = np.random.choice(["SETTLED", "PENDING", "FAILED"], n, p=[0.85, 0.10, 0.05])
    countries = np.random.choice(["US", "GB", "CA", "AU", "DE"], n)
    mccs = np.random.choice(["5411", "5812", "5999", "7011", "5541"], n)
    
    # Generate card BINs (from reference)
    bins = np.random.choice(["411111", "424242", "512345", "543210", "378282"], n)
    card_numbers = [f"{bin_}{random.randint(1000000000, 9999999999)}" for bin_ in bins]
    
    merchant_ids = [f"MERCH{random.randint(1000, 9999)}" for _ in range(n)]
    auth_codes = [f"AUTH{random.randint(100000, 999999)}" for _ in range(n)]
    
    df = pd.DataFrame({
        "txn_id": txn_ids,
        "event_time": event_times,
        "settlement_time": settlement_times,
        "amount": amounts,
        "currency": currencies,
        "status": statuses,
        "country": countries,
        "mcc": mccs,
        "card_number": card_numbers,
        "merchant_id": merchant_ids,
        "auth_code": auth_codes
    })
    
    # Add settlement_date for SETTLED transactions
    df["settlement_date"] = df.apply(
        lambda row: row["settlement_time"].date() if row["status"] == "SETTLED" else None,
        axis=1
    )
    
    df.to_csv("sample_data/transactions_batch1.csv", index=False)
    print(f"✓ Generated transactions_batch1.csv ({len(df)} rows) - GOOD QUALITY")


def generate_transactions_batch2(n=1000):
    """Generate bad quality transactions batch with specific issues."""
    np.random.seed(123)
    random.seed(123)
    
    # Generate transaction IDs (with duplicates)
    txn_ids = [f"TXN{str(i).zfill(8)}" for i in range(1, n+1)]
    # Inject 0.8% duplicates
    dup_count = int(n * 0.008)
    for i in range(dup_count):
        idx = random.randint(0, n-1)
        txn_ids[idx] = txn_ids[random.randint(0, n-1)]
    
    # Generate timestamps
    base_time = datetime.now() - timedelta(hours=48)  # Older batch
    event_times = [base_time + timedelta(seconds=random.randint(0, 7200)) for _ in range(n)]
    settlement_times = [et + timedelta(hours=random.randint(1, 72)) for et in event_times]  # Longer delays
    
    # Generate amounts
    amounts = np.random.lognormal(3, 1.5, n).round(2)
    amounts = np.clip(amounts, 1, 10000)
    
    # Generate currencies
    currencies = np.random.choice(["USD", "EUR", "GBP", "JPY", "CAD", "XXX"], n, p=[0.45, 0.2, 0.15, 0.1, 0.05, 0.05])
    
    # DON'T adjust JPY amounts (introduce decimal error)
    for i, curr in enumerate(currencies):
        if curr == "JPY" and random.random() < 0.05:  # 5% have incorrect decimals
            amounts[i] = round(amounts[i], 2)  # Should be whole number
    
    # Generate other fields
    statuses = np.random.choice(["SETTLED", "PENDING", "FAILED"], n, p=[0.80, 0.12, 0.08])
    countries = np.random.choice(["US", "GB", "CA", "AU", "DE", "ZZ"], n, p=[0.4, 0.2, 0.15, 0.15, 0.05, 0.05])
    
    # Invalid MCCs
    valid_mccs = ["5411", "5812", "5999", "7011", "5541"]
    invalid_mccs = ["999", "12345", "ABCD"]
    mccs = []
    for _ in range(n):
        if random.random() < 0.03:  # 3% invalid
            mccs.append(random.choice(invalid_mccs))
        else:
            mccs.append(random.choice(valid_mccs))
    
    # Generate card BINs (some not in reference)
    known_bins = ["411111", "424242", "512345", "543210", "378282"]
    unknown_bins = ["999999", "888888", "777777"]
    bins = []
    for _ in range(n):
        if random.random() < 0.05:  # 5% unknown BINs
            bins.append(random.choice(unknown_bins))
        else:
            bins.append(random.choice(known_bins))
    
    card_numbers = [f"{bin_}{random.randint(1000000000, 9999999999)}" for bin_ in bins]
    
    merchant_ids = [f"MERCH{random.randint(1000, 9999)}" for _ in range(n)]
    
    # Missing auth_codes (3-5%)
    auth_codes = []
    for _ in range(n):
        if random.random() < 0.04:
            auth_codes.append(None)
        else:
            auth_codes.append(f"AUTH{random.randint(100000, 999999)}")
    
    df = pd.DataFrame({
        "txn_id": txn_ids,
        "event_time": event_times,
        "settlement_time": settlement_times,
        "amount": amounts,
        "currency": currencies,
        "status": statuses,
        "country": countries,
        "mcc": mccs,
        "card_number": card_numbers,
        "merchant_id": merchant_ids,
        "auth_code": auth_codes
    })
    
    # Add settlement_date for SETTLED transactions (but miss some)
    df["settlement_date"] = df.apply(
        lambda row: row["settlement_time"].date() if row["status"] == "SETTLED" and random.random() > 0.03 else None,
        axis=1
    )
    
    df.to_csv("sample_data/transactions_batch2.csv", index=False)
    print(f"✓ Generated transactions_batch2.csv ({len(df)} rows) - BAD QUALITY")


def generate_settlement_ledger(n=950):
    """Generate settlement ledger (with some mismatches)."""
    np.random.seed(42)
    random.seed(42)
    
    # Generate transaction IDs (mostly matching batch1)
    txn_ids = [f"TXN{str(i).zfill(8)}" for i in range(1, n+1)]
    
    # Generate amounts
    amounts = np.random.lognormal(3, 1.5, n).round(2)
    amounts = np.clip(amounts, 1, 10000)
    
    # Generate currencies
    currencies = np.random.choice(["USD", "EUR", "GBP", "JPY", "CAD"], n, p=[0.5, 0.2, 0.15, 0.1, 0.05])
    
    # Adjust JPY amounts
    for i, curr in enumerate(currencies):
        if curr == "JPY":
            amounts[i] = round(amounts[i] * 100)
    
    # Introduce 1-2% amount mismatches
    for i in range(int(n * 0.015)):
        idx = random.randint(0, n-1)
        amounts[idx] += random.uniform(-10, 10)
    
    settlement_dates = [(datetime.now() - timedelta(days=random.randint(0, 7))).date() for _ in range(n)]
    
    df = pd.DataFrame({
        "txn_id": txn_ids,
        "amount": amounts,
        "currency": currencies,
        "settlement_date": settlement_dates
    })
    
    df.to_csv("sample_data/settlement.csv", index=False)
    print(f"✓ Generated settlement.csv ({len(df)} rows)")


if __name__ == "__main__":
    print("\n🔧 Generating sample datasets...\n")
    
    generate_bin_reference()
    generate_currency_rules()
    generate_mcc_codes()
    generate_transactions_batch1(1000)
    generate_transactions_batch2(1000)
    generate_settlement_ledger(950)
    
    print("\n✅ All sample datasets generated successfully!")
    print("📁 Output directory: sample_data/")
    print("\nGenerated files:")
    print("  - bin_reference.csv")
    print("  - currency_rules.csv")
    print("  - mcc_codes.csv")
    print("  - transactions_batch1.csv (good quality)")
    print("  - transactions_batch2.csv (bad quality)")
    print("  - settlement.csv")
