import requests
import pandas as pd
import tempfile
import os
import logging
import re
import time
import platform
from requests.exceptions import SSLError

class GoogleSheetsClient:
    """Client to fetch data from Google Sheets as Excel (preserves formatting)"""

    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        # Use requests.Session for connection pooling and better performance
        self.session = requests.Session()
        # gspread client for write operations (lazy loaded)
        self._gspread_client = None

    def __del__(self):
        """Clean up resources on deletion"""
        if hasattr(self, 'session'):
            self.session.close()

    @staticmethod
    def _safe_remove_temp_file(tmp_path, max_retries=3):
        """
        Safely remove temp file with retry logic for Windows file locking

        Args:
            tmp_path: Path to temporary file
            max_retries: Number of retry attempts
        """
        for attempt in range(max_retries):
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
                return  # Success
            except (PermissionError, OSError) as e:
                if attempt < max_retries - 1:
                    # Wait a bit and retry (Windows file locking issue)
                    time.sleep(0.1 * (attempt + 1))
                else:
                    # Last attempt failed, log warning but don't crash
                    # The temp file will be cleaned up by OS eventually
                    if platform.system() == "Windows":
                        # This is expected on Windows sometimes
                        pass
                    else:
                        raise

    @staticmethod
    def extract_spreadsheet_id(sheet_url):
        """
        Extract spreadsheet ID from Google Sheets URL

        Supports formats:
        - https://docs.google.com/spreadsheets/d/SHEET_ID/edit
        - https://docs.google.com/spreadsheets/d/SHEET_ID/edit#gid=0
        - SHEET_ID (if already just ID)
        """
        if not sheet_url:
            raise ValueError("Sheet URL is empty")

        # If it's already just an ID (no slashes), return it
        if '/' not in sheet_url:
            return sheet_url

        # Extract from URL
        match = re.search(r'/spreadsheets/d/([a-zA-Z0-9-_]+)', sheet_url)
        if match:
            return match.group(1)

        raise ValueError(f"Could not extract spreadsheet ID from URL: {sheet_url}")

    def _build_export_url(self, spreadsheet_id):
        """Build Google Sheets Excel export URL

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID

        Returns:
            Export URL string
        """
        return f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=xlsx"

    def _download_with_ssl_retry(self, url, log_messages=True):
        """Download URL with SSL error retry logic

        Args:
            url: URL to download
            log_messages: Whether to log download messages

        Returns:
            requests.Response object

        Raises:
            requests.exceptions.RequestException on failure
        """
        try:
            if log_messages:
                self.logger.info("Downloading with SSL verification...")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response
        except SSLError:
            if log_messages:
                self.logger.warning("SSL verification failed. Retrying without verification...")
            response = self.session.get(url, verify=False, timeout=30)
            response.raise_for_status()
            return response

    def _save_response_to_temp_file(self, response):
        """Save HTTP response content to temporary Excel file

        Args:
            response: requests.Response object with Excel content

        Returns:
            Path to temporary file
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
            tmp_file.write(response.content)
            return tmp_file.name

    def _download_excel(self, spreadsheet_id, log_messages=True):
        """Download Google Sheets as Excel file

        Args:
            spreadsheet_id: Google Sheets spreadsheet ID
            log_messages: Whether to log download messages

        Returns:
            Path to temporary Excel file
        """
        url = self._build_export_url(spreadsheet_id)
        response = self._download_with_ssl_retry(url, log_messages)
        return self._save_response_to_temp_file(response)

    def _dataframe_to_rows(self, df):
        """Convert pandas DataFrame to list of rows

        Args:
            df: pandas DataFrame

        Returns:
            List of rows, where each row is a list of string values
        """
        rows = []
        for _, row in df.iterrows():
            row_data = []
            for i in range(len(df.columns)):
                cell_value = row.iloc[i]
                if pd.notna(cell_value):
                    row_data.append(str(cell_value))
                else:
                    row_data.append("")
            rows.append(row_data)
        return rows

    def _get_available_sheets(self, tmp_path):
        """Get list of available sheet names from Excel file

        Args:
            tmp_path: Path to temporary Excel file

        Returns:
            List of sheet names
        """
        with pd.ExcelFile(tmp_path) as excel_file:
            return excel_file.sheet_names

    def _cleanup_temp_file_on_error(self, tmp_path, exception):
        """Clean up temporary file and re-raise exception

        Args:
            tmp_path: Path to temporary file
            exception: Exception to re-raise
        """
        if os.path.exists(tmp_path):
            self._safe_remove_temp_file(tmp_path)
        raise exception

    def get_sheet_metadata(self, spreadsheet_id):
        """
        Get sheet metadata including title and all tab names with GIDs

        Returns:
            dict with 'title' and 'sheets' list
        """
        try:
            # Download as Excel to get all sheets
            tmp_path = self._download_excel(spreadsheet_id, log_messages=False)

            try:
                # Read Excel file to get sheet names
                sheet_names = self._get_available_sheets(tmp_path)

                # Clean up
                self._safe_remove_temp_file(tmp_path)

                # Note: We can't get the actual Google Sheet title or GIDs from Excel export
                # The Excel file only has sheet names, not GIDs
                # We'll need to use sheet names directly with pandas

                return {
                    'spreadsheet_id': spreadsheet_id,
                    'sheet_names': sheet_names
                }

            except Exception as e:
                self._cleanup_temp_file_on_error(tmp_path, e)

        except Exception as e:
            raise Exception(f"Failed to get sheet metadata: {str(e)}")

    def fetch_messages_by_tab_name(self, sheet_url, tab_name):
        """
        Download messages from a specific tab by name

        Args:
            sheet_url: Full Google Sheets URL
            tab_name: Name of the tab/sheet

        Returns:
            List of rows from that tab
        """
        spreadsheet_id = self.extract_spreadsheet_id(sheet_url)

        self.logger.info(f"Downloading tab '{tab_name}' from Google Sheets: {spreadsheet_id}")

        try:
            # Download entire workbook as Excel
            tmp_path = self._download_excel(spreadsheet_id, log_messages=True)

            try:
                # Read specific sheet by name
                df = pd.read_excel(tmp_path, sheet_name=tab_name)

                # Convert to list of rows
                rows = self._dataframe_to_rows(df)

                # Get available sheet names for error messaging
                available_sheets = self._get_available_sheets(tmp_path)

                # Clean up
                self._safe_remove_temp_file(tmp_path)

                if not rows:
                    raise Exception(f"Tab '{tab_name}' is empty")

                self.logger.info(f"Successfully downloaded {len(rows)} rows from tab '{tab_name}'")

                return rows, available_sheets

            except ValueError as e:
                # Sheet name not found
                available_sheets = self._get_available_sheets(tmp_path)
                self._safe_remove_temp_file(tmp_path)

                raise Exception(
                    f"Tab '{tab_name}' not found.\n"
                    f"Available tabs: {', '.join(available_sheets)}"
                )
            except Exception as e:
                self._cleanup_temp_file_on_error(tmp_path, e)

        except Exception as e:
            raise Exception(f"Failed to download tab '{tab_name}': {str(e)}")

    def fetch_messages(self, spreadsheet_id, sheet_gid=0):
        """
        Download messages from a Google Sheet as Excel

        Args:
            spreadsheet_id: The Google Sheet ID from the URL
            sheet_gid: The sheet GID (default 0 for first sheet)

        Returns:
            List of rows, where each row is [first_message, followup_message]

        Raises:
            Exception: If download fails or sheet is not accessible
        """
        try:
            self.logger.info(f"Downloading messages from Google Sheets: {spreadsheet_id}")

            # Download entire workbook as Excel
            tmp_path = self._download_excel(spreadsheet_id, log_messages=True)

            try:
                # Read Excel file with pandas (preserves all formatting)
                df = pd.read_excel(tmp_path, sheet_name=sheet_gid if sheet_gid > 0 else 0)

                # Convert to list of rows
                rows = self._dataframe_to_rows(df)

                # Clean up temp file
                self._safe_remove_temp_file(tmp_path)

                if not rows:
                    raise Exception("Google Sheet is empty")

                self.logger.info(f"Successfully downloaded {len(rows)} message variants from Google Sheets")

                return rows

            except Exception as e:
                self._cleanup_temp_file_on_error(tmp_path, e)

        except requests.exceptions.Timeout:
            raise Exception("Timeout while downloading from Google Sheets. Check your internet connection.")
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise Exception("Google Sheet not found. Check the spreadsheet ID.")
            elif e.response.status_code == 403:
                raise Exception("Access denied. Make sure the sheet is shared with 'Anyone with the link can view'.")
            else:
                raise Exception(f"HTTP error while downloading Google Sheet: {e}")
        except Exception as e:
            raise Exception(f"Failed to download from Google Sheets: {str(e)}")

    def validate_connection(self, spreadsheet_id, sheet_gid=0):
        """
        Test if the Google Sheet can be accessed

        Returns:
            Tuple of (success: bool, message: str, row_count: int)
        """
        try:
            rows = self.fetch_messages(spreadsheet_id, sheet_gid)
            return True, f"Successfully connected! Found {len(rows)} message variants", len(rows)
        except Exception as e:
            return False, str(e), 0

    # =========================================================================
    # WRITE OPERATIONS (requires gspread library and authentication)
    # =========================================================================

    def _get_gspread_client(self):
        """
        Get or create gspread client for write operations
        Requires gspread library and credentials

        Returns:
            gspread client instance
        """
        if self._gspread_client is not None:
            return self._gspread_client

        try:
            import gspread
            from google.oauth2.service_account import Credentials
        except ImportError:
            raise Exception(
                "gspread library not found. Install with: pip install gspread google-auth"
            )

        # Try to load credentials from common locations
        creds_paths = [
            'credentials.json',
            'config/credentials.json',
            os.path.expanduser('~/.config/gspread/credentials.json'),
            os.path.expanduser('~/credentials.json')
        ]

        credentials = None
        for path in creds_paths:
            if os.path.exists(path):
                self.logger.info(f"Loading Google Sheets credentials from: {path}")
                scopes = [
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
                credentials = Credentials.from_service_account_file(path, scopes=scopes)
                break

        if not credentials:
            raise Exception(
                "Google Sheets credentials not found.\n"
                "Please download service account JSON from Google Cloud Console\n"
                "and save as 'credentials.json' in the project root.\n"
                f"Searched paths: {creds_paths}"
            )

        self._gspread_client = gspread.authorize(credentials)
        return self._gspread_client

    def write_to_tab(self, sheet_url, tab_name, data):
        """
        Write data to a specific tab in Google Sheets
        Creates tab if it doesn't exist, otherwise overwrites

        Args:
            sheet_url: Google Sheets URL
            tab_name: Name of the tab to write to
            data: List of lists, where each inner list is a row
                  Example: [['Name', 'Phone'], ['John', '123'], ['Jane', '456']]
        """
        try:
            import gspread

            gc = self._get_gspread_client()
            spreadsheet_id = self.extract_spreadsheet_id(sheet_url)

            # Open spreadsheet
            spreadsheet = gc.open_by_key(spreadsheet_id)

            # Check if tab exists
            try:
                worksheet = spreadsheet.worksheet(tab_name)
                # Clear existing data
                worksheet.clear()
                self.logger.info(f"Cleared existing tab '{tab_name}'")
            except gspread.exceptions.WorksheetNotFound:
                # Create new tab
                worksheet = spreadsheet.add_worksheet(
                    title=tab_name,
                    rows=len(data) + 100,  # Extra rows for future
                    cols=max(len(row) for row in data) if data else 10
                )
                self.logger.info(f"Created new tab '{tab_name}'")

            # Write data
            if data:
                worksheet.update('A1', data)
                self.logger.info(f"✅ Wrote {len(data)} rows to tab '{tab_name}'")

        except ImportError:
            raise Exception("gspread not installed. This is required for write operations.")
        except Exception as e:
            raise Exception(f"Failed to write to tab '{tab_name}': {str(e)}")
