"""Tests for assets/assets.py"""

import pytest
from unittest.mock import patch

from dagster import MaterializeResult, build_asset_context

from src.markets_data_hub.assets.assets import riksbank_certificate


def _make_valid_raw_record():
    """Returns a raw record that passes transform_record and schema validation."""
    return {
        "Anbudsdag": "2024-01-15",
        "Likviddag": "2024-01-17",
        "Förfallodag": "2024-04-15",
        "Räntesats": "3.75",
        "Erbjuden volym SEK Md": "20",
        "Totalt budbelopp SEK Md": "18",
        "Tilldelad volym SEK Md": "17",
        "Antal bud": "5",
        "Tilldelningsprocent": "85.0",
        "ISIN": "SE0012345678",
        "source_url": "https://example.com",
    }


class TestRiksbankCertificateAsset:
    """Tests for the riksbank_certificate Dagster asset."""

    @patch("src.markets_data_hub.assets.assets.scrape_rb_cert_auctions")
    def test_returns_materialize_result(self, mock_scrape, tmp_path):
        mock_scrape.return_value = [_make_valid_raw_record()]

        with patch("src.markets_data_hub.assets.assets.DATA_DIR", tmp_path):
            context = build_asset_context()
            result = riksbank_certificate(context)

        assert isinstance(result, MaterializeResult)

    @patch("src.markets_data_hub.assets.assets.scrape_rb_cert_auctions")
    def test_metadata_contains_num_records(self, mock_scrape, tmp_path):
        mock_scrape.return_value = [_make_valid_raw_record()]

        with patch("src.markets_data_hub.assets.assets.DATA_DIR", tmp_path):
            context = build_asset_context()
            result = riksbank_certificate(context)

        assert "num_records" in result.metadata
        assert "path" in result.metadata

    @patch("src.markets_data_hub.assets.assets.scrape_rb_cert_auctions")
    def test_one_valid_record_gives_num_records_one(self, mock_scrape, tmp_path):
        mock_scrape.return_value = [_make_valid_raw_record()]

        with patch("src.markets_data_hub.assets.assets.DATA_DIR", tmp_path):
            context = build_asset_context()
            result = riksbank_certificate(context)

        assert result.metadata["num_records"] == 1

    @patch("src.markets_data_hub.assets.assets.scrape_rb_cert_auctions")
    def test_invalid_records_are_skipped(self, mock_scrape, tmp_path):
        # One valid record + one error record (missing required fields)
        mock_scrape.return_value = [
            _make_valid_raw_record(),
            {"auction_date": "2024-01-15", "source_url": "https://x.com", "error": "HTTP 404"},
        ]

        with patch("src.markets_data_hub.assets.assets.DATA_DIR", tmp_path):
            context = build_asset_context()
            result = riksbank_certificate(context)

        assert result.metadata["num_records"] == 1

    @patch("src.markets_data_hub.assets.assets.scrape_rb_cert_auctions")
    def test_empty_scrape_result_gives_zero_records(self, mock_scrape, tmp_path):
        mock_scrape.return_value = []

        with patch("src.markets_data_hub.assets.assets.DATA_DIR", tmp_path):
            context = build_asset_context()
            result = riksbank_certificate(context)

        assert result.metadata["num_records"] == 0

    @patch("src.markets_data_hub.assets.assets.scrape_rb_cert_auctions")
    def test_parquet_file_is_written(self, mock_scrape, tmp_path):
        mock_scrape.return_value = [_make_valid_raw_record()]

        with patch("src.markets_data_hub.assets.assets.DATA_DIR", tmp_path):
            context = build_asset_context()
            riksbank_certificate(context)

        assert (tmp_path / "rb_cert_auctions_result.parquet").exists()

    @patch("src.markets_data_hub.assets.assets.scrape_rb_cert_auctions")
    def test_multiple_valid_records(self, mock_scrape, tmp_path):
        record = _make_valid_raw_record()
        mock_scrape.return_value = [record, record]

        with patch("src.markets_data_hub.assets.assets.DATA_DIR", tmp_path):
            context = build_asset_context()
            result = riksbank_certificate(context)

        assert result.metadata["num_records"] == 2

    @patch("src.markets_data_hub.assets.assets.scrape_rb_cert_auctions")
    def test_scrape_called_with_limit_zero(self, mock_scrape, tmp_path):
        mock_scrape.return_value = []

        with patch("src.markets_data_hub.assets.assets.DATA_DIR", tmp_path):
            context = build_asset_context()
            riksbank_certificate(context)

        mock_scrape.assert_called_once_with(limit=0)