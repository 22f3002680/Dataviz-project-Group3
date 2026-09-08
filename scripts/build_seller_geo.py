"""Export seller geo-coordinates for the 'alternative seller' suggestion feature.

Aggregates the geolocation dataset to the ZIP-code-prefix level (mean lat/lng,
matching the project's cleaning note) and joins it to sellers, producing
seller_geo.csv (seller_id, seller_state, lat, lng).
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
WORKBOOK = ROOT / "Dataviz_proj_all_datasets.xlsx"
OUT = ROOT / "metabase" / "data" / "seller_geo.csv"


def main() -> None:
    book = pd.ExcelFile(WORKBOOK)
    geo = pd.read_excel(book, sheet_name="geolocation_dataset")
    sellers = pd.read_excel(book, sheet_name="sellers_dataset")
    book.close()

    geo_zip = (
        geo.groupby("geolocation_zip_code_prefix")
        .agg(lat=("geolocation_lat", "mean"), lng=("geolocation_lng", "mean"))
        .reset_index()
    )
    merged = sellers.merge(
        geo_zip,
        left_on="seller_zip_code_prefix",
        right_on="geolocation_zip_code_prefix",
        how="left",
    )
    out = merged[["seller_id", "seller_state", "lat", "lng"]].dropna(subset=["lat", "lng"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT, index=False)
    print(f"Wrote {len(out):,} sellers with coordinates "
          f"({len(sellers) - len(out):,} missing) -> {OUT}")


if __name__ == "__main__":
    main()
