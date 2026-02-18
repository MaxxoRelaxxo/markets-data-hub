# src/markets_data_hub/definitions.py

from dagster import Definitions

from .assets.assets import riksbank_certificate, sales_of_gov_bonds

defs = Definitions(
    assets=[
        riksbank_certificate,
        sales_of_gov_bonds
    ],
)