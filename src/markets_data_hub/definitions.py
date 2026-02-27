# src/markets_data_hub/definitions.py

from dagster import (
    AssetSelection,
    EnvVar,
    Definitions,
    ScheduleDefinition,
    define_asset_job,
)
from markets_data_hub.utils.functions import SwestrApiResource, SweaApiResource

swestr_resource = SwestrApiResource(api_key=EnvVar("RIKSBANK_API_KEY"))
swea_api = SweaApiResource(api_key=EnvVar("RIKSBANK_API_KEY"))

from .assets.assets import (
    riksbank_certificate,
    sales_of_gov_bonds,
    get_swestr_values,
    get_policy_rate_values,
    mortgage_rates,
    deposit_rates,
    nfc_lending_rates,
)
from .assets.frontend import build_frontend

riksbank_certificate_job = define_asset_job(
    name="riksbank_certificate_job",
    selection=AssetSelection.assets(riksbank_certificate),
)

sales_of_gov_bonds_job = define_asset_job(
    name="sales_of_gov_bonds_job",
    selection=AssetSelection.assets(sales_of_gov_bonds),
)

swestr_job = define_asset_job(
    name="swestr_job",
    selection=AssetSelection.assets(get_swestr_values),
)

policy_rate_job = define_asset_job(
    name="policy_rate_job",
    selection=AssetSelection.assets(get_policy_rate_values),
)

build_frontend_job = define_asset_job(
    name="build_frontend_job",
    selection=AssetSelection.assets(build_frontend),
)

riksbank_certificate_schedule = ScheduleDefinition(
    name="riksbank_certificate_weekly",
    target=riksbank_certificate_job,
    cron_schedule="40 10 * * 2",  # Every Tuesday at 10:40
)

sales_of_gov_bonds_schedule = ScheduleDefinition(
    name="sales_of_gov_bonds_weekly",
    target=sales_of_gov_bonds_job,
    cron_schedule="40 10 * * 5",  # Every Friday at 10:40
)

swestr_schedule = ScheduleDefinition(
    name="swestr_weekday",
    target=swestr_job,
    cron_schedule="5 9 * * 1-5",  # Every weekday at 09:05
)

policy_rate_schedule = ScheduleDefinition(
    name="swea_weekday",
    target=policy_rate_job,
    cron_schedule="5 9 * * 1-5",  # Every weekday at 09:05
)

build_frontend_schedule = ScheduleDefinition(
    name="build_frontend_weekly",
    target=build_frontend_job,
    cron_schedule="0 11 * * 5",  # Every Friday at 11:00 (after data jobs finish)
)

defs = Definitions(
    assets=[
        riksbank_certificate,
        sales_of_gov_bonds,
        get_swestr_values,
        get_policy_rate_values,
        build_frontend,
        mortgage_rates,
        deposit_rates,
        nfc_lending_rates
    ],
    jobs=[riksbank_certificate_job, sales_of_gov_bonds_job, swestr_job, policy_rate_job, build_frontend_job],
    schedules=[
        riksbank_certificate_schedule,
        sales_of_gov_bonds_schedule,
        swestr_schedule,
        policy_rate_schedule,
        build_frontend_schedule,
    ],
    resources={
        "swestr_api": swestr_resource,
        "swea_api" : swea_api
    },
)