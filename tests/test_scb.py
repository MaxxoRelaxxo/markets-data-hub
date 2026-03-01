"""Tests for SCB data fetching (fetch_scb and _jsonstat2_to_df)."""

import pytest
from unittest.mock import patch, MagicMock

import polars as pl
from requests.exceptions import HTTPError

from src.markets_data_hub.utils.functions import fetch_scb, _jsonstat2_to_df


# ── Fixtures ─────────────────────────────────────────────────────────────────


def _make_jsonstat2_response(dims, dim_data, values):
    """Build a minimal JSON-stat2 payload.

    Args:
        dims: list of dimension id strings, e.g. ["Region", "Tid"]
        dim_data: dict mapping dim id -> dict with "index" and "label"
        values: flat list of numeric values
    """
    dimension = {}
    for dim_id in dims:
        d = dim_data[dim_id]
        dimension[dim_id] = {
            "category": {
                "index": d["index"],
                "label": d["label"],
            }
        }
    return {"id": dims, "dimension": dimension, "value": values}


SIMPLE_RESPONSE = _make_jsonstat2_response(
    dims=["Region", "Tid"],
    dim_data={
        "Region": {
            "index": {"01": 0, "02": 1},
            "label": {"01": "Stockholm", "02": "Göteborg"},
        },
        "Tid": {
            "index": {"2024M01": 0, "2024M02": 1},
            "label": {"2024M01": "2024M01", "2024M02": "2024M02"},
        },
    },
    values=[1.5, 2.0, 3.1, 4.2],
)


# ── _jsonstat2_to_df ─────────────────────────────────────────────────────────


class TestJsonstat2ToDf:
    def test_returns_polars_dataframe(self):
        result = _jsonstat2_to_df(SIMPLE_RESPONSE)
        assert isinstance(result, pl.DataFrame)

    def test_correct_column_names(self):
        result = _jsonstat2_to_df(SIMPLE_RESPONSE)
        assert set(result.columns) == {"Region", "Tid", "value"}

    def test_correct_row_count(self):
        result = _jsonstat2_to_df(SIMPLE_RESPONSE)
        # 2 regions × 2 time periods = 4 rows
        assert len(result) == 4

    def test_values_are_preserved(self):
        result = _jsonstat2_to_df(SIMPLE_RESPONSE)
        assert result["value"].to_list() == [1.5, 2.0, 3.1, 4.2]

    def test_dimension_labels_are_used(self):
        result = _jsonstat2_to_df(SIMPLE_RESPONSE)
        assert "Stockholm" in result["Region"].to_list()
        assert "Göteborg" in result["Region"].to_list()

    def test_cartesian_product_of_dimensions(self):
        result = _jsonstat2_to_df(SIMPLE_RESPONSE)
        stockholm_rows = result.filter(pl.col("Region") == "Stockholm")
        assert len(stockholm_rows) == 2
        assert set(stockholm_rows["Tid"].to_list()) == {"2024M01", "2024M02"}

    def test_single_dimension(self):
        data = _make_jsonstat2_response(
            dims=["Tid"],
            dim_data={
                "Tid": {
                    "index": {"2024M01": 0},
                    "label": {"2024M01": "Jan 2024"},
                }
            },
            values=[99.9],
        )
        result = _jsonstat2_to_df(data)
        assert len(result) == 1
        assert result["Tid"][0] == "Jan 2024"
        assert result["value"][0] == 99.9

    def test_three_dimensions(self):
        data = _make_jsonstat2_response(
            dims=["A", "B", "C"],
            dim_data={
                "A": {"index": {"a1": 0, "a2": 1}, "label": {"a1": "A1", "a2": "A2"}},
                "B": {"index": {"b1": 0}, "label": {"b1": "B1"}},
                "C": {"index": {"c1": 0, "c2": 1}, "label": {"c1": "C1", "c2": "C2"}},
            },
            values=[10, 20, 30, 40],
        )
        result = _jsonstat2_to_df(data)
        # 2 × 1 × 2 = 4 rows
        assert len(result) == 4
        assert set(result.columns) == {"A", "B", "C", "value"}

    def test_dimension_order_matches_index(self):
        """Dimension categories should be ordered by their index, not alphabetically."""
        data = _make_jsonstat2_response(
            dims=["Var"],
            dim_data={
                "Var": {
                    "index": {"z": 0, "a": 1},
                    "label": {"z": "Zebra", "a": "Aardvark"},
                }
            },
            values=[1.0, 2.0],
        )
        result = _jsonstat2_to_df(data)
        assert result["Var"].to_list() == ["Zebra", "Aardvark"]

    def test_without_index_uses_label_key_order(self):
        """When 'index' is absent, fallback to label key ordering."""
        dimension = {
            "X": {
                "category": {
                    "label": {"k1": "First", "k2": "Second"},
                }
            }
        }
        data = {"id": ["X"], "dimension": dimension, "value": [10, 20]}
        result = _jsonstat2_to_df(data)
        assert len(result) == 2
        assert result["X"].to_list() == ["First", "Second"]

    def test_null_values_in_data(self):
        data = _make_jsonstat2_response(
            dims=["Tid"],
            dim_data={
                "Tid": {
                    "index": {"t1": 0, "t2": 1},
                    "label": {"t1": "Period 1", "t2": "Period 2"},
                }
            },
            values=[1.5, None],
        )
        result = _jsonstat2_to_df(data)
        assert len(result) == 2
        assert result["value"][0] == 1.5
        assert result["value"][1] is None


# ── fetch_scb ────────────────────────────────────────────────────────────────


class TestFetchScb:
    @patch("src.markets_data_hub.utils.functions.requests.get")
    def test_returns_dataframe(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SIMPLE_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = fetch_scb(
            table_id="TAB1234",
            selection={"Region": ["01"]},
        )
        assert isinstance(result, pl.DataFrame)

    @patch("src.markets_data_hub.utils.functions.requests.get")
    def test_builds_correct_url(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SIMPLE_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        fetch_scb(table_id="TAB5783", selection={"Tid": ["*"]})

        call_args = mock_get.call_args
        assert call_args[0][0] == "https://statistikdatabasen.scb.se/api/v2/tables/TAB5783/data"

    @patch("src.markets_data_hub.utils.functions.requests.get")
    def test_passes_lang_and_format_params(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SIMPLE_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        fetch_scb(table_id="TAB1", selection={"X": ["1"]}, lang="en", output_format="csv")

        params = mock_get.call_args[1]["params"]
        assert params["lang"] == "en"
        assert params["outputFormat"] == "csv"

    @patch("src.markets_data_hub.utils.functions.requests.get")
    def test_selection_mapped_to_valuecodes_params(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SIMPLE_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        fetch_scb(
            table_id="TAB1",
            selection={"ContentsCode": ["000004ZW"], "Tid": ["*"]},
        )

        params = mock_get.call_args[1]["params"]
        assert params["valueCodes[ContentsCode]"] == "000004ZW"
        assert params["valueCodes[Tid]"] == "*"

    @patch("src.markets_data_hub.utils.functions.requests.get")
    def test_multiple_values_joined_with_comma(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SIMPLE_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        fetch_scb(
            table_id="TAB1",
            selection={"Region": ["01", "02", "03"]},
        )

        params = mock_get.call_args[1]["params"]
        assert params["valueCodes[Region]"] == "01,02,03"

    @patch("src.markets_data_hub.utils.functions.requests.get")
    def test_raises_on_http_error(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = HTTPError("404 Not Found")
        mock_get.return_value = mock_resp

        with pytest.raises(HTTPError):
            fetch_scb(table_id="INVALID", selection={"X": ["1"]})

    @patch("src.markets_data_hub.utils.functions.requests.get")
    def test_default_lang_is_sv(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SIMPLE_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        fetch_scb(table_id="TAB1", selection={"X": ["1"]})

        params = mock_get.call_args[1]["params"]
        assert params["lang"] == "sv"

    @patch("src.markets_data_hub.utils.functions.requests.get")
    def test_default_output_format_is_jsonstat2(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SIMPLE_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        fetch_scb(table_id="TAB1", selection={"X": ["1"]})

        params = mock_get.call_args[1]["params"]
        assert params["outputFormat"] == "json-stat2"

    @patch("src.markets_data_hub.utils.functions.requests.get")
    def test_empty_selection_still_works(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SIMPLE_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = fetch_scb(table_id="TAB1", selection={})
        assert isinstance(result, pl.DataFrame)

    @patch("src.markets_data_hub.utils.functions.requests.get")
    def test_realistic_mortgage_rate_response(self, mock_get):
        """Simulates a realistic SCB mortgage-rate API response."""
        data = _make_jsonstat2_response(
            dims=["ContentsCode", "Referenssektor", "Motpartssektor", "Avtal", "Rantebindningstid", "Tid"],
            dim_data={
                "ContentsCode": {
                    "index": {"000004ZW": 0},
                    "label": {"000004ZW": "Ränta (procent)"},
                },
                "Referenssektor": {
                    "index": {"1": 0},
                    "label": {"1": "MFI"},
                },
                "Motpartssektor": {
                    "index": {"2c": 0},
                    "label": {"2c": "Hushåll"},
                },
                "Avtal": {
                    "index": {"0200": 0},
                    "label": {"0200": "nya och omförhandlade avtal"},
                },
                "Rantebindningstid": {
                    "index": {"rörligt": 0, "1-5": 1},
                    "label": {
                        "rörligt": "T.o.m. 3 månader (rörligt)",
                        "1-5": "Över ett till fem år (1-5 år)",
                    },
                },
                "Tid": {
                    "index": {"2024M01": 0, "2024M02": 1},
                    "label": {"2024M01": "2024M01", "2024M02": "2024M02"},
                },
            },
            values=[4.52, 4.48, 3.91, 3.85],
        )
        mock_resp = MagicMock()
        mock_resp.json.return_value = data
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        result = fetch_scb(
            table_id="TAB5783",
            selection={
                "ContentsCode": ["000004ZW"],
                "Referenssektor": ["1"],
                "Motpartssektor": ["2c"],
                "Avtal": ["0200"],
                "Rantebindningstid": ["*"],
                "Tid": ["*"],
            },
        )
        # 1×1×1×1×2 binding periods × 2 time periods = 4 rows
        assert len(result) == 4
        assert "Rantebindningstid" in result.columns
        assert "Tid" in result.columns
        assert "value" in result.columns
        assert result["value"].to_list() == [4.52, 4.48, 3.91, 3.85]
