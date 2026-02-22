# src/markets_data_hub/definitions.py

from dagster import (
    AssetSelection,
    EnvVar,
    Definitions,
    ScheduleDefinition,
    define_asset_job,
)
from markets_data_hub.utils.functions import SwestrApiResource

swestr_resource = SwestrApiResource(api_key=EnvVar("RIKSBANK_API_KEY"))

from .assets.assets import (
    riksbank_certificate,
    sales_of_gov_bonds,
    get_swestr_values
)

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

swestr_job = define_asset_job(
    name="swestr_job",
    selection=AssetSelection.assets(get_swestr_values),
)

swestr_schedule = ScheduleDefinition(
    name="swestr_weekday",
    target=swestr_job,
    cron_schedule="5 9 * * 1-5",  # Every weekday at 09:05
)

defs = Definitions(
    assets=[
        riksbank_certificate,
        sales_of_gov_bonds,
        get_swestr_values
    ],
    jobs=[swestr_job],
    schedules=[
        riksbank_certificate_schedule,
        sales_of_gov_bonds_schedule,
        swestr_schedule,
    ],
    resources={"swestr_api": swestr_resource},
)