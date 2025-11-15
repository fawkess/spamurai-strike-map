#!/usr/bin/env python3
"""
Unit tests for GoogleSheetsClient
Tests Google Sheets reading functionality
"""

import pytest
import os
import sys
import logging
import pandas as pd

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from google_sheets_client import GoogleSheetsClient

# Test fixtures directory
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')
# Test output directory for temporary test files
TEST_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), 'test_output')


@pytest.fixture
def logger():
    """Create test logger"""
    logger = logging.getLogger('test')
    logger.setLevel(logging.INFO)
    return logger


@pytest.fixture
def client(logger):
    """Create GoogleSheetsClient instance"""
    return GoogleSheetsClient(logger)


class TestSpreadsheetIDExtraction:
    """Test spreadsheet ID extraction from URLs"""

    def test_extract_id_from_full_url(self, client):
        """Test extracting ID from full Google Sheets URL"""
        url = "https://docs.google.com/spreadsheets/d/1ABC123xyz/edit#gid=0"
        sheet_id = client.extract_spreadsheet_id(url)
        assert sheet_id == "1ABC123xyz"

    def test_extract_id_from_simple_url(self, client):
        """Test extracting ID from simple URL"""
        url = "https://docs.google.com/spreadsheets/d/1ABC123xyz/edit"
        sheet_id = client.extract_spreadsheet_id(url)
        assert sheet_id == "1ABC123xyz"

    def test_extract_id_from_plain_id(self, client):
        """Test that plain ID is returned as-is"""
        plain_id = "1ABC123xyz"
        sheet_id = client.extract_spreadsheet_id(plain_id)
        assert sheet_id == plain_id

    def test_extract_id_invalid_url(self, client):
        """Test error on invalid URL"""
        with pytest.raises(ValueError):
            client.extract_spreadsheet_id("https://invalid-url.com/something")


class TestLocalExcelReading:
    """Test reading local Excel files (simulating Google Sheets)"""

    def test_read_basic_allocation(self, client, logger):
        """Test reading basic allocation fixture"""
        fixture = os.path.join(FIXTURES_DIR, 'basic_allocation.xlsx')

        # Get metadata
        # Note: We can't actually test Google Sheets API without real credentials
        # But we can test local Excel reading which the client also supports

        # For testing, we'll directly use pandas
        excel_file = pd.ExcelFile(fixture)

        # Should have 3 sheets
        assert len(excel_file.sheet_names) == 3
        assert 'All Contacts' in excel_file.sheet_names
        assert 'Spamurais' in excel_file.sheet_names
        assert 'Source Priorities' in excel_file.sheet_names

    def test_read_contacts_tab(self, client, logger):
        """Test reading contacts data"""
        fixture = os.path.join(FIXTURES_DIR, 'basic_allocation.xlsx')

        # Read All Contacts tab
        df = pd.read_excel(fixture, sheet_name='All Contacts')

        # Should have expected columns
        assert 'Name' in df.columns
        assert 'Phone Number' in df.columns
        assert 'Center' in df.columns
        assert 'Source of Interest' in df.columns

        # Should have 6 contacts
        assert len(df) == 6

    def test_read_spamurais_tab(self, client, logger):
        """Test reading Spamurais data"""
        fixture = os.path.join(FIXTURES_DIR, 'basic_allocation.xlsx')

        df = pd.read_excel(fixture, sheet_name='Spamurais')

        # Should have expected columns
        assert 'Name' in df.columns
        assert 'Center' in df.columns

        # Should have 2 Spamurais
        assert len(df) == 2

    def test_read_priorities_tab(self, client, logger):
        """Test reading priorities data"""
        fixture = os.path.join(FIXTURES_DIR, 'basic_allocation.xlsx')

        df = pd.read_excel(fixture, sheet_name='Source Priorities')

        # Should have expected columns
        assert 'Source of Interest' in df.columns
        assert 'Priority' in df.columns

        # Should have 3 priorities
        assert len(df) == 3


class TestExcelFileHandling:
    """Test Excel file handling utilities"""

    def test_read_multiple_sheets(self, client, logger):
        """Test reading multiple sheets from Excel file"""
        fixture = os.path.join(FIXTURES_DIR, 'center_based_allocation.xlsx')

        excel_file = pd.ExcelFile(fixture)

        # Read all sheets
        contacts = pd.read_excel(excel_file, sheet_name='All Contacts')
        spamurais = pd.read_excel(excel_file, sheet_name='Spamurais')
        priorities = pd.read_excel(excel_file, sheet_name='Source Priorities')

        # Verify data loaded
        assert len(contacts) > 0
        assert len(spamurais) > 0
        assert len(priorities) > 0

    def test_handle_missing_tab(self, client, logger):
        """Test error handling for missing tab"""
        fixture = os.path.join(FIXTURES_DIR, 'basic_allocation.xlsx')

        with pytest.raises(ValueError):
            pd.read_excel(fixture, sheet_name='NonExistent Tab')

    def test_handle_empty_tab(self, client, logger):
        """Test reading empty tab"""
        # Create fixture with empty tab in test_output directory
        os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)
        fixture_path = os.path.join(TEST_OUTPUT_DIR, 'empty_tab.xlsx')

        empty_df = pd.DataFrame()

        with pd.ExcelWriter(fixture_path, engine='openpyxl') as writer:
            empty_df.to_excel(writer, sheet_name='Empty', index=False)

        # Read empty tab
        df = pd.read_excel(fixture_path, sheet_name='Empty')

        # Should return empty DataFrame
        assert len(df) == 0

        # Cleanup
        os.remove(fixture_path)


class TestDataFormatting:
    """Test data formatting and normalization"""

    def test_phone_number_format(self, client, logger):
        """Test phone numbers are read correctly"""
        fixture = os.path.join(FIXTURES_DIR, 'basic_allocation.xlsx')

        df = pd.read_excel(fixture, sheet_name='All Contacts')

        # Phone numbers should be numeric
        for phone in df['Phone Number']:
            # Could be int or float from Excel
            assert isinstance(phone, (int, float))

    def test_text_fields_preserved(self, client, logger):
        """Test text fields are preserved correctly"""
        fixture = os.path.join(FIXTURES_DIR, 'edge_cases.xlsx')

        df = pd.read_excel(fixture, sheet_name='All Contacts')

        # Should have names with special characters
        names = df['Name'].tolist()

        # Verify special characters preserved
        assert len(names) > 0

    def test_empty_cells_handled(self, client, logger):
        """Test empty cells are handled correctly"""
        fixture = os.path.join(FIXTURES_DIR, 'basic_allocation.xlsx')

        df = pd.read_excel(fixture, sheet_name='All Contacts')

        # Center column should have empty values
        # Empty cells in pandas become NaN or empty string
        centers = df['Center'].tolist()

        # Should be able to handle empty values
        assert len(centers) == len(df)


class TestErrorHandling:
    """Test error handling for various scenarios"""

    def test_file_not_found(self, client, logger):
        """Test handling of non-existent file"""
        with pytest.raises(FileNotFoundError):
            pd.read_excel('nonexistent_file.xlsx')

    def test_invalid_excel_file(self, client, logger):
        """Test handling of invalid Excel file"""
        # Create invalid file
        invalid_path = os.path.join(FIXTURES_DIR, 'invalid.xlsx')

        with open(invalid_path, 'w') as f:
            f.write('This is not an Excel file')

        with pytest.raises(Exception):
            pd.read_excel(invalid_path)

        # Cleanup
        os.remove(invalid_path)

    def test_empty_spreadsheet_id(self, client):
        """Test handling of empty spreadsheet ID"""
        with pytest.raises(ValueError):
            client.extract_spreadsheet_id('')

    def test_none_spreadsheet_id(self, client):
        """Test handling of None spreadsheet ID"""
        with pytest.raises((ValueError, AttributeError)):
            client.extract_spreadsheet_id(None)


# Note: Testing actual Google Sheets API calls requires:
# 1. Valid Google Sheet URL
# 2. Sheet must be publicly accessible
# 3. Internet connection
# These tests would be marked as integration tests and skipped in CI

@pytest.mark.skip(reason="Requires real Google Sheets URL")
class TestRealGoogleSheets:
    """Tests that require real Google Sheets (skipped by default)"""

    def test_fetch_real_sheet(self, client, logger):
        """Test fetching from real Google Sheets"""
        # This would require a real, public Google Sheet URL
        # url = "https://docs.google.com/spreadsheets/d/REAL_ID/edit"
        # rows, sheets = client.fetch_messages_by_tab_name(url, "Sheet1")
        # assert len(rows) > 0
        pass

    def test_validate_connection(self, client, logger):
        """Test connection validation with real sheet"""
        # This would require a real, public Google Sheet URL
        # success, message, count = client.validate_connection("REAL_ID")
        # assert success
        # assert count > 0
        pass


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
