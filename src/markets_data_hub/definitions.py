# src/markets_data_hub/definitions.py

from dagster import (
    AssetSelection,
    Definitions,
    ScheduleDefinition,
)

from .assets.assets import riksbank_certificate, sales_of_gov_bonds

riksbank_certificate_schedule = ScheduleDefinition(
    name="riksbank_certificate_weekly",
    target=AssetSelection.assets(riksbank_certificate),
    cron_schedule="40 10 * * 2",  # Every Tuesday at 10:40
)

sales_of_gov_bonds_schedule = ScheduleDefinition(
    name="sales_of_gov_bonds_weekly",
    target=AssetSelection.assets(sales_of_gov_bonds),
    cron_schedule="40 10 * * 5",  # Every Friday at 10:40
)

defs = Definitions(
    assets=[
        riksbank_certificate,
        sales_of_gov_bonds,
    ],
    schedules=[
        riksbank_certificate_schedule,
        sales_of_gov_bonds_schedule,
    ],
)