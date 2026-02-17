from src.markets_data_hub.definitions import defs


def test_def_can_load():
    assert defs.get_job_def("all_assets_job")
