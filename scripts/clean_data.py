import os
import re
import numpy as np
import pandas as pd

INPUT_FILE = "data/processed/merged_raw_data.csv"
OUTPUT_FILE = "data/processed/cleaned_data.csv"


# ----------------------------
# LOAD
# ----------------------------
def load_data() -> pd.DataFrame:
    print("Loading merged data...")
    df = pd.read_csv(INPUT_FILE, low_memory=False)
    print("Loaded shape:", df.shape)
    return df


# ----------------------------
# HELPERS
# ----------------------------
def normalize_text(value):
    if pd.isna(value):
        return np.nan
    value = str(value).strip()
    if value == "" or value.lower() in {"nan", "none", "null"}:
        return np.nan
    return value


def safe_lower(value):
    value = normalize_text(value)
    if pd.isna(value):
        return np.nan
    return str(value).strip().lower()


# ----------------------------
# 1. DATE CLEANING
# ----------------------------
def parse_mixed_date(value):
    if pd.isna(value):
        return pd.NaT

    value = str(value).strip()
    if value == "":
        return pd.NaT

    # common invalid placeholders
    if value.lower() in {"nan", "null", "none", "not available"}:
        return pd.NaT

    # try day-first and non-day-first parsing
    parsed_1 = pd.to_datetime(value, errors="coerce", dayfirst=True)
    parsed_2 = pd.to_datetime(value, errors="coerce", dayfirst=False)

    if not pd.isna(parsed_1):
        return parsed_1
    if not pd.isna(parsed_2):
        return parsed_2

    return pd.NaT


def clean_dates(df: pd.DataFrame) -> pd.DataFrame:
    print("\n[1] Cleaning dates...")
    if "order_date" in df.columns:
        df["order_date"] = df["order_date"].apply(parse_mixed_date)
        # standardize to YYYY-MM-DD string only if you want a flat stored format
        df["order_date"] = df["order_date"].dt.strftime("%Y-%m-%d")
    return df


# ----------------------------
# 2. PRICE CLEANING
# ----------------------------
def parse_price(value):
    if pd.isna(value):
        return np.nan

    value = str(value).strip()
    if value == "":
        return np.nan

    lowered = value.lower()
    invalid_tokens = {
        "price on request", "on request", "na", "n/a", "null", "none", "nan", "-", "--"
    }
    if lowered in invalid_tokens:
        return np.nan

    # remove currency symbols, spaces, commas and text
    cleaned = value.replace("₹", "").replace(",", "").strip()
    cleaned = re.sub(r"[^\d.\-]", "", cleaned)

    if cleaned in {"", ".", "-", "-.", ".-"}:
        return np.nan

    try:
        return float(cleaned)
    except ValueError:
        return np.nan


def clean_price(df: pd.DataFrame) -> pd.DataFrame:
    print("[2] Cleaning price columns...")

    price_cols = ["original_price_inr", "final_amount_inr", "delivery_charges"]
    for col in price_cols:
        if col in df.columns:
            df[col] = df[col].apply(parse_price)

    return df


# ----------------------------
# 3. RATING CLEANING
# ----------------------------
def parse_rating(value):
    if pd.isna(value):
        return np.nan

    value = str(value).strip().lower()
    if value in {"", "na", "n/a", "null", "none", "nan"}:
        return np.nan

    # 4 stars, 4star
    star_match = re.search(r"(\d+(\.\d+)?)\s*star", value)
    if star_match:
        rating = float(star_match.group(1))
        return rating if 0 <= rating <= 5 else np.nan

    # 3/5 or 2.5/5.0
    frac_match = re.search(r"(\d+(\.\d+)?)\s*/\s*(\d+(\.\d+)?)", value)
    if frac_match:
        num = float(frac_match.group(1))
        den = float(frac_match.group(3))
        if den > 0:
            rating = (num / den) * 5
            return round(rating, 2) if 0 <= rating <= 5 else np.nan

    # plain numeric like 5.0
    num_match = re.search(r"(\d+(\.\d+)?)", value)
    if num_match:
        rating = float(num_match.group(1))
        return rating if 0 <= rating <= 5 else np.nan

    return np.nan


def clean_ratings(df: pd.DataFrame) -> pd.DataFrame:
    print("[3] Cleaning ratings...")

    rating_cols = ["customer_rating", "product_rating", "rating"]
    for col in rating_cols:
        if col in df.columns:
            df[col] = df[col].apply(parse_rating)

    return df


# ----------------------------
# 4. CITY CLEANING
# ----------------------------
def normalize_city_name(value):
    value = safe_lower(value)
    if pd.isna(value):
        return np.nan

    value = re.sub(r"[^a-z\s]", "", value)
    value = re.sub(r"\s+", " ", value).strip()

    city_map = {
        "bangalore": "bengaluru",
        "bengaluru": "bengaluru",
        "bombay": "mumbai",
        "mumbai": "mumbai",
        "new delhi": "delhi",
        "delhi": "delhi",
        "madras": "chennai",
        "calcutta": "kolkata",
        "trivandrum": "thiruvananthapuram",
        "cochin": "kochi",
        "baroda": "vadodara",
        "poona": "pune",
        "gurgaon": "gurugram",
        "noida": "noida",
        "banglore": "bengaluru",
        "bengalure": "bengaluru",
        "mumbay": "mumbai",
        "mumabai": "mumbai",
        "delhii": "delhi",
        "chennaii": "chennai",
        "hyderbad": "hyderabad",
        "ahmedabad city": "ahmedabad",
    }

    if value in city_map:
        return city_map[value]

    return value


def clean_city(df: pd.DataFrame) -> pd.DataFrame:
    print("[4] Cleaning city names...")

    if "customer_city" in df.columns:
        df["customer_city"] = df["customer_city"].apply(normalize_city_name)

    return df


# ----------------------------
# 5. BOOLEAN CLEANING
# ----------------------------
def parse_boolean(value):
    if pd.isna(value):
        return np.nan

    value = str(value).strip().lower()

    true_values = {"true", "yes", "1", "y", "t"}
    false_values = {"false", "no", "0", "n", "f"}

    if value in true_values:
        return True
    if value in false_values:
        return False

    return np.nan


def clean_booleans(df: pd.DataFrame) -> pd.DataFrame:
    print("[5] Cleaning boolean columns...")

    bool_cols = ["is_prime_member", "is_prime_eligible", "is_festival_sale"]
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].apply(parse_boolean)

    return df


# ----------------------------
# 6. CATEGORY CLEANING
# ----------------------------
def normalize_category(value):
    value = safe_lower(value)
    if pd.isna(value):
        return np.nan

    value = value.replace("&", "and")
    value = re.sub(r"[^a-z\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()

    category_map = {
        "electronic": "electronics",
        "electronics": "electronics",
        "electronicss": "electronics",
        "electronics accessories": "electronics and accessories",
        "electronics and accessories": "electronics and accessories",
        "electronic accessories": "electronics and accessories",

        "fashion": "fashion",
        "clothings": "fashion",
        "clothing": "fashion",
        "apparel": "fashion",

        "home kitchen": "home and kitchen",
        "home and kitchen": "home and kitchen",
        "kitchen": "home and kitchen",

        "beauty personal care": "beauty and personal care",
        "beauty and personal care": "beauty and personal care",

        "grocery": "grocery",
        "groceries": "grocery",

        "books": "books",
        "book": "books",

        "sports": "sports",
        "sports fitness": "sports and fitness",
        "sports and fitness": "sports and fitness",
    }

    return category_map.get(value, value)


def clean_category(df: pd.DataFrame) -> pd.DataFrame:
    print("[6] Cleaning categories...")

    category_cols = ["category", "category_catalog"]
    for col in category_cols:
        if col in df.columns:
            df[col] = df[col].apply(normalize_category)

    return df


# ----------------------------
# 7. DELIVERY DAYS CLEANING
# ----------------------------
def parse_delivery_days(value):
    if pd.isna(value):
        return np.nan

    value = str(value).strip().lower()
    if value in {"", "na", "n/a", "null", "none", "nan"}:
        return np.nan

    if "same day" in value:
        return 0
    if "next day" in value:
        return 1

    # 1-2 days -> use upper bound or average; here average is cleaner
    range_match = re.search(r"(\d+)\s*-\s*(\d+)", value)
    if range_match:
        low = int(range_match.group(1))
        high = int(range_match.group(2))
        return round((low + high) / 2, 1)

    num_match = re.search(r"(\d+(\.\d+)?)", value)
    if num_match:
        days = float(num_match.group(1))
        if days < 0:
            return np.nan
        return days

    return np.nan


def clean_delivery_days(df: pd.DataFrame) -> pd.DataFrame:
    print("[7] Cleaning delivery days...")

    if "delivery_days" in df.columns:
        df["delivery_days"] = df["delivery_days"].apply(parse_delivery_days)

        # remove unrealistic values
        df.loc[df["delivery_days"] < 0, "delivery_days"] = np.nan
        df.loc[df["delivery_days"] > 30, "delivery_days"] = np.nan

    return df


# ----------------------------
# 8. DUPLICATE HANDLING
# ----------------------------
def handle_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    print("[8] Handling duplicates...")

    before = len(df)

    # exact duplicates first
    df = df.drop_duplicates()

    # smarter duplicate logic:
    # if same customer_id + product_id + order_date + final_amount_inr repeats many times,
    # treat rows with same transaction_id as true duplicate,
    # but keep rows without transaction_id because they may be genuine bulk orders unless fully identical.
    if all(col in df.columns for col in ["customer_id", "product_id", "order_date", "final_amount_inr"]):
        key_cols = ["customer_id", "product_id", "order_date", "final_amount_inr"]

        if "transaction_id" in df.columns:
            # same transaction_id repeated = data error
            df = df.drop_duplicates(subset=["transaction_id"], keep="first")
        else:
            # if no transaction_id, only drop duplicates when the full key + source_file is same
            extra_cols = key_cols.copy()
            if "source_file" in df.columns:
                extra_cols.append("source_file")
            df = df.drop_duplicates(subset=extra_cols, keep="first")

    after = len(df)
    print(f"Removed {before - after} duplicate rows")

    return df


# ----------------------------
# 9. OUTLIER HANDLING
# ----------------------------
def cap_or_correct_outliers(df: pd.DataFrame) -> pd.DataFrame:
    print("[9] Handling price outliers...")

    target_col = "final_amount_inr"
    if target_col not in df.columns:
        return df

    # product/category median-based correction for extreme entry issues
    group_col = None
    if "product_id" in df.columns:
        group_col = "product_id"
    elif "category_catalog" in df.columns:
        group_col = "category_catalog"
    elif "category" in df.columns:
        group_col = "category"

    if group_col:
        group_median = df.groupby(group_col)[target_col].transform("median")

        # detect 100x-style problems relative to group median
        condition_high = (df[target_col] > group_median * 20) & group_median.notna()
        condition_low = (df[target_col] < group_median / 20) & group_median.notna() & (df[target_col] > 0)

        # try decimal-point correction
        df.loc[condition_high, target_col] = df.loc[condition_high, target_col] / 100
        df.loc[condition_low, target_col] = df.loc[condition_low, target_col] * 100

    # final IQR cleanup
    q1 = df[target_col].quantile(0.25)
    q3 = df[target_col].quantile(0.75)
    iqr = q3 - q1

    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    df.loc[df[target_col] < lower, target_col] = np.nan
    df.loc[df[target_col] > upper, target_col] = np.nan

    return df


# ----------------------------
# 10. PAYMENT METHOD CLEANING
# ----------------------------
def normalize_payment_method(value):
    value = safe_lower(value)
    if pd.isna(value):
        return np.nan

    value = value.replace("_", " ").replace(".", " ")
    value = re.sub(r"\s+", " ", value).strip()

    payment_map = {
        "upi": "upi",
        "phonepe": "upi",
        "googlepay": "upi",
        "google pay": "upi",
        "paytm upi": "upi",

        "credit card": "card",
        "debit card": "card",
        "card": "card",
        "cc": "card",
        "creditcard": "card",
        "debitcard": "card",

        "cash on delivery": "cod",
        "cod": "cod",
        "c o d": "cod",

        "net banking": "net banking",
        "netbanking": "net banking",

        "wallet": "wallet",
        "amazon pay": "wallet",
        "paytm wallet": "wallet",
    }

    return payment_map.get(value, value)


def clean_payment_method(df: pd.DataFrame) -> pd.DataFrame:
    print("[10] Cleaning payment methods...")

    if "payment_method" in df.columns:
        df["payment_method"] = df["payment_method"].apply(normalize_payment_method)

    return df


# ----------------------------
# MISSING VALUE STRATEGY
# ----------------------------
def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    print("Applying strategic missing-value handling...")

    # ratings: leave as NaN if missing
    # booleans: leave as NaN if unclear
    # delivery days: leave as NaN if unknown

    # price fields: keep NaN if truly unusable
    # optional light imputation
    if "customer_rating" in df.columns:
        median_rating = df["customer_rating"].median()
        if not pd.isna(median_rating):
            df["customer_rating"] = df["customer_rating"].fillna(median_rating)

    return df


# ----------------------------
# SAVE
# ----------------------------
def save_cleaned_data(df: pd.DataFrame) -> None:
    os.makedirs("data/processed", exist_ok=True)
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"\nCleaned data saved to: {OUTPUT_FILE}")


# ----------------------------
# REPORT
# ----------------------------
def print_summary(df: pd.DataFrame) -> None:
    print("\nCleaning summary:")
    print("Final shape:", df.shape)

    cols_to_check = [
        "order_date",
        "original_price_inr",
        "final_amount_inr",
        "customer_rating",
        "customer_city",
        "category",
        "payment_method",
        "delivery_days",
    ]

    for col in cols_to_check:
        if col in df.columns:
            print(f"\nColumn: {col}")
            print(df[col].head(10))


# ----------------------------
# MAIN
# ----------------------------
def main():
    df = load_data()

    df = clean_dates(df)
    df = clean_price(df)
    df = clean_ratings(df)
    df = clean_city(df)
    df = clean_booleans(df)
    df = clean_category(df)
    df = clean_delivery_days(df)
    df = handle_duplicates(df)
    df = cap_or_correct_outliers(df)
    df = clean_payment_method(df)
    df = handle_missing_values(df)

    save_cleaned_data(df)
    print_summary(df)


if __name__ == "__main__":
    main()