# src/markets_data_hub/definitions.py

from datetime import date, timedelta

from dagster import (
    AssetSelection,
    EnvVar,
    Definitions,
    RunRequest,
    ScheduleDefinition,
    ScheduleEvaluationContext,
    define_asset_job,
    schedule,
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
from .assets.sync import GitHubRepoResource, sync_data_to_github


# ---------------------------------------------------------------------------
# Swedish banking-day helper (Mon-Fri excl. public holidays)
# ---------------------------------------------------------------------------

def _swedish_public_holidays(year: int) -> set[date]:
    """Return the set of Swedish public holidays for a given year."""
    # Easter calculation (Anonymous Gregorian algorithm)
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    easter = date(year, month, day)

    # Midsummer Day = Saturday in [Jun 20, Jun 26]
    jun20 = date(year, 6, 20)
    midsummer_day = jun20 + timedelta(days=(5 - jun20.weekday()) % 7)
    midsummer_eve = midsummer_day - timedelta(days=1)

    # All Saints' Day = Saturday in [Oct 31, Nov 6]
    oct31 = date(year, 10, 31)
    all_saints = oct31 + timedelta(days=(5 - oct31.weekday()) % 7)

    return {
        date(year, 1, 1),                       # Nyårsdagen
        date(year, 1, 6),                        # Trettondedag jul
        easter - timedelta(days=2),              # Långfredagen
        easter,                                  # Påskdagen
        easter + timedelta(days=1),              # Annandag påsk
        date(year, 5, 1),                        # Första maj
        easter + timedelta(days=39),             # Kristi himmelsfärdsdag
        date(year, 6, 6),                        # Nationaldagen
        midsummer_eve,                           # Midsommarafton
        midsummer_day,                           # Midsommardagen
        all_saints,                              # Alla helgons dag
        date(year, 12, 24),                      # Julafton
        date(year, 12, 25),                      # Juldagen
        date(year, 12, 26),                      # Annandag jul
        date(year, 12, 31),                      # Nyårsafton
    }


def _is_banking_day(d: date) -> bool:
    return d.weekday() < 5 and d not in _swedish_public_holidays(d.year)


def _nth_banking_day(year: int, month: int, n: int) -> date:
    """Return the n-th banking day (1-indexed) of the given month."""
    d = date(year, month, 1)
    count = 0
    while True:
        if _is_banking_day(d):
            count += 1
            if count == n:
                return d
        d += timedelta(days=1)
        if d.month != month:
            raise ValueError(f"Month {year}-{month:02d} has fewer than {n} banking days")


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

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

scb_data_job = define_asset_job(
    name="scb_data_job",
    selection=AssetSelection.assets(mortgage_rates, deposit_rates, nfc_lending_rates),
)

# Sync jobs – fetch data and push Parquet to GitHub in one execution.
# Assets not in the selection are treated as previously materialised.
daily_sync_job = define_asset_job(
    name="daily_sync_job",
    selection=AssetSelection.assets(
        get_swestr_values, get_policy_rate_values, sync_data_to_github,
    ),
)

full_sync_job = define_asset_job(
    name="full_sync_job",
    selection=AssetSelection.assets(
        riksbank_certificate,
        sales_of_gov_bonds,
        get_swestr_values,
        get_policy_rate_values,
        mortgage_rates,
        deposit_rates,
        nfc_lending_rates,
        sync_data_to_github,
    ),
)


# ---------------------------------------------------------------------------
# Schedules
# ---------------------------------------------------------------------------

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


@schedule(
    cron_schedule="5 9 * * 1-5",  # Evaluate every weekday at 09:05
    job=scb_data_job,
)
def scb_data_schedule(context: ScheduleEvaluationContext):
    """Fetch SCB rates on the 19th banking day of each month."""
    today = context.scheduled_execution_time.date()
    try:
        target = _nth_banking_day(today.year, today.month, 19)
    except ValueError:
        return
    if today == target:
        yield RunRequest()


# Sync schedules – fetch data + push Parquet to GitHub → triggers Pages deploy

daily_sync_schedule = ScheduleDefinition(
    name="daily_sync",
    target=daily_sync_job,
    cron_schedule="30 9 * * 1-5",  # Weekdays 09:30 (after API jobs)
)

full_sync_schedule = ScheduleDefinition(
    name="full_sync_weekly",
    target=full_sync_job,
    cron_schedule="30 11 * * 5",  # Fridays 11:30 (after scraping jobs)
)


github_repo = GitHubRepoResource(
    token=EnvVar("GITHUB_TOKEN"),
    owner=EnvVar("GITHUB_OWNER"),
    repo=EnvVar("GITHUB_REPO"),
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
        nfc_lending_rates,
        sync_data_to_github,
    ],
    jobs=[
        riksbank_certificate_job,
        sales_of_gov_bonds_job,
        swestr_job,
        policy_rate_job,
        build_frontend_job,
        scb_data_job,
        daily_sync_job,
        full_sync_job,
    ],
    schedules=[
        riksbank_certificate_schedule,
        sales_of_gov_bonds_schedule,
        swestr_schedule,
        policy_rate_schedule,
        build_frontend_schedule,
        scb_data_schedule,
        daily_sync_schedule,
        full_sync_schedule,
    ],
    resources={
        "swestr_api": swestr_resource,
        "swea_api": swea_api,
        "github_repo": github_repo,
    },
)