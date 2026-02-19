from src.markets_data_hub.definitions import defs


def test_def_can_load():
    assert defs.has_implicit_global_asset_job_def


def test_schedules_are_registered():
    assert defs.get_schedule_def("riksbank_certificate_weekly")
    assert defs.get_schedule_def("sales_of_gov_bonds_weekly")
