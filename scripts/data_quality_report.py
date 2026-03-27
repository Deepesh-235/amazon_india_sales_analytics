import os
import pandas as pd
import numpy as np

INPUT_FILE = "data/processed/cleaned_data.csv"
OUTPUT_DIR = "outputs/reports"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "data_quality_report.csv")


def load_data():
    print("Loading cleaned data...")
    df = pd.read_csv(INPUT_FILE, low_memory=False)
    print("Loaded shape:", df.shape)
    return df


def missing_values_report(df):
    report = pd.DataFrame({
        "column": df.columns,
        "missing_count": df.isna().sum().values,
        "missing_percent": (df.isna().sum().values / len(df)) * 100
    })
    report["issue_type"] = "missing_values"
    return report


def duplicate_report(df):
    full_dupes = int(df.duplicated().sum())

    key_dupes = None
    key_cols = ["customer_id", "product_id", "order_date", "final_amount_inr"]
    if all(col in df.columns for col in key_cols):
        key_dupes = int(df.duplicated(subset=key_cols).sum())

    report = pd.DataFrame([
        {"column": "full_row_duplicates", "missing_count": full_dupes, "missing_percent": np.nan, "issue_type": "duplicates"},
        {"column": "key_based_duplicates", "missing_count": key_dupes, "missing_percent": np.nan, "issue_type": "duplicates"},
    ])
    return report


def outlier_report(df):
    rows = []
    numeric_cols = ["original_price_inr", "final_amount_inr", "discount_percent", "delivery_days", "customer_rating"]

    for col in numeric_cols:
        if col in df.columns:
            series = pd.to_numeric(df[col], errors="coerce").dropna()
            if len(series) > 0:
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                outlier_count = int(((series < lower) | (series > upper)).sum())

                rows.append({
                    "column": col,
                    "missing_count": outlier_count,
                    "missing_percent": (outlier_count / len(df)) * 100,
                    "issue_type": "outliers"
                })

    return pd.DataFrame(rows)


def invalid_date_report(df):
    if "order_date" not in df.columns:
        return pd.DataFrame()

    parsed = pd.to_datetime(df["order_date"], errors="coerce")
    invalid_count = int(parsed.isna().sum())

    return pd.DataFrame([{
        "column": "order_date",
        "missing_count": invalid_count,
        "missing_percent": (invalid_count / len(df)) * 100,
        "issue_type": "invalid_dates"
    }])


def build_summary(df):
    parts = [
        missing_values_report(df),
        duplicate_report(df),
        outlier_report(df),
        invalid_date_report(df)
    ]
    summary = pd.concat(parts, ignore_index=True)
    return summary


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    df = load_data()
    summary = build_summary(df)

    summary.to_csv(OUTPUT_FILE, index=False)

    print("\nData Quality Report Generated:")
    print(summary.head(20))
    print(f"\nSaved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()