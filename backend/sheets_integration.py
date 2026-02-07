"""
NexusLog Google Sheets Integration
Syncs content ideas to Google Sheets
"""
import os
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import List, Dict


class SheetsIntegration:
    """Google Sheets integration for content ideas"""
    
    def __init__(self):
        self.credentials_path = os.getenv('GOOGLE_SHEETS_CREDENTIALS_PATH')
        self.sheet_id = os.getenv('GOOGLE_SHEET_ID')
        
        if not self.credentials_path or not self.sheet_id:
            raise ValueError("Google Sheets credentials or sheet ID not configured")
            
        # Robust path handling
        if not os.path.exists(self.credentials_path):
            # Try looking one directory up (common issue when running from backend dir)
            alt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'credentials', 'google-sheets-creds.json')
            if os.path.exists(alt_path):
                self.credentials_path = alt_path
            else:
                # Try absolute path resolution relative to backend
                alt_path_2 = os.path.join(os.path.dirname(__file__), '../credentials/google-sheets-creds.json')
                if os.path.exists(alt_path_2):
                     self.credentials_path = alt_path_2
        
        # Initialize credentials
        self.credentials = service_account.Credentials.from_service_account_file(
            self.credentials_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        
        self.service = build('sheets', 'v4', credentials=self.credentials)
    
    def append_content_idea(self, idea_description: str, ai_prompt: str, output_types: List[str]) -> bool:
        """
        Append a content idea to the Google Sheet
        Format: [Timestamp, Idea Description, AI Prompt, Output Types]
        """
        try:
            from datetime import datetime
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            output_types_str = ", ".join(output_types) if output_types else "Not specified"
            
            values = [[timestamp, idea_description, ai_prompt, output_types_str]]
            
            body = {
                'values': values
            }
            
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.sheet_id,
                range="'Post Ideas'!A:D",  # Adjust range as needed
                valueInputOption='RAW',
                body=body
            ).execute()
            
            print(f"Added {result.get('updates').get('updatedCells')} cells to sheet")
            return True
        
        except HttpError as error:
            print(f"Google Sheets API error: {error}")
            return False
        except Exception as e:
            print(f"Error appending to sheet: {e}")
            return False
    
    def get_all_ideas(self) -> List[Dict]:
        """Retrieve all content ideas from the sheet"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range="'Post Ideas'!A:D"
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                return []
            
            # Convert to dict format
            ideas = []
            for row in values[1:]:  # Skip header row
                if len(row) >= 4:
                    ideas.append({
                        'timestamp': row[0],
                        'idea_description': row[1],
                        'ai_prompt': row[2],
                        'output_types': row[3]
                    })
            
            return ideas
        
        except HttpError as error:
            print(f"Google Sheets API error: {error}")
            return []
        except Exception as e:
            print(f"Error reading from sheet: {e}")
            return []
    
    def create_header_if_needed(self):
        """Create header row if sheet is empty"""
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range="'Post Ideas'!A1:D1"
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                # Sheet is empty, add header
                header = [['Timestamp', 'Idea Description', 'AI Prompt', 'Output Types']]
                body = {'values': header}
                
                self.service.spreadsheets().values().update(
                    spreadsheetId=self.sheet_id,
                    range="'Post Ideas'!A1:D1",
                    valueInputOption='RAW',
                    body=body
                ).execute()
                
                print("Created header row in Google Sheet")
        
        except Exception as e:
            print(f"Error creating header: {e}")
    
    def find_row_by_values(self, sheet_name: str, identifier_columns: List[str], 
                           identifier_values: List[str], data_range: str = None) -> int:
        """
        Find a row by matching values in multiple columns.
        
        Args:
            sheet_name: Name of the sheet tab (e.g., 'Stock Tracker')
            identifier_columns: Column letters to match (e.g., ['A', 'B'] for date + stock name)
            identifier_values: Values to find in those columns (e.g., ['2026-02-07', 'RELIANCE'])
            data_range: Optional specific range to search (defaults to columns A-Z)
        
        Returns:
            Row number (1-indexed) if found, -1 if not found
        """
        try:
            # Determine search range
            if data_range:
                search_range = f"'{sheet_name}'!{data_range}"
            else:
                # Default: search all data up to column Z
                search_range = f"'{sheet_name}'!A:Z"
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.sheet_id,
                range=search_range
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                return -1
            
            # Convert column letters to indices (A=0, B=1, etc.)
            col_indices = [ord(col.upper()) - ord('A') for col in identifier_columns]
            
            # Search each row
            for row_idx, row in enumerate(values):
                # Check if all identifier values match
                matches = True
                for col_idx, expected_value in zip(col_indices, identifier_values):
                    if col_idx >= len(row):
                        matches = False
                        break
                    # Case-insensitive, trimmed comparison
                    if str(row[col_idx]).strip().lower() != str(expected_value).strip().lower():
                        matches = False
                        break
                
                if matches:
                    return row_idx + 1  # Return 1-indexed row number
            
            return -1  # Not found
            
        except HttpError as error:
            print(f"Google Sheets API error in find_row_by_values: {error}")
            return -1
        except Exception as e:
            print(f"Error finding row: {e}")
            return -1
    
    def update_cell_by_identifiers(
        self,
        sheet_name: str,
        identifier_columns: List[str],
        identifier_values: List[str],
        target_column: str,
        new_value: str,
        sheet_id: str = None
    ) -> Dict:
        """
        Generic cell update - finds a row by identifier columns and updates a target column.
        
        Use case example (Stock Sheet):
            - identifier_columns: ['A', 'B'] (Date, Stock Name)
            - identifier_values: ['2026-02-07', 'RELIANCE']
            - target_column: 'L' (Comment/Notes column)
            - new_value: 'Positive momentum, watch resistance at 2850'
        
        Args:
            sheet_name: Tab name (e.g., 'Stock Tracker', 'Post Ideas')
            identifier_columns: Columns to match for row finding
            identifier_values: Values to match in those columns
            target_column: Column letter to update (e.g., 'L')
            new_value: Value to write to the cell
            sheet_id: Optional override sheet ID (uses default if None)
        
        Returns:
            Dict with 'success', 'message', and 'row' (if found)
        """
        try:
            # Use override sheet_id or default
            active_sheet_id = sheet_id or self.sheet_id
            
            # Find the row
            row_num = self.find_row_by_values(sheet_name, identifier_columns, identifier_values)
            
            if row_num == -1:
                return {
                    'success': False,
                    'message': f"Row not found for identifiers: {dict(zip(identifier_columns, identifier_values))}",
                    'row': None
                }
            
            # Build cell reference (e.g., 'Stock Tracker'!L5)
            cell_ref = f"'{sheet_name}'!{target_column.upper()}{row_num}"
            
            # Update the cell
            body = {'values': [[new_value]]}
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=active_sheet_id,
                range=cell_ref,
                valueInputOption='USER_ENTERED',  # Allows formulas and auto-formatting
                body=body
            ).execute()
            
            updated_cells = result.get('updatedCells', 0)
            
            return {
                'success': True,
                'message': f"Updated {cell_ref} with value (updated {updated_cells} cell)",
                'row': row_num,
                'cell_reference': cell_ref
            }
            
        except HttpError as error:
            return {
                'success': False,
                'message': f"Google Sheets API error: {error}",
                'row': None
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"Error updating cell: {e}",
                'row': None
            }
    
    def update_stock_note(self, date: str, stock_name: str, note: str, 
                          sheet_name: str = "Stock Tracker", column: str = "L") -> Dict:
        """
        Convenience method for updating stock notes.
        
        Args:
            date: Date string (format should match sheet, e.g., '2026-02-07' or '07-02-2026')
            stock_name: Stock symbol or name (case-insensitive)
            note: The note/comment to add
            sheet_name: Sheet tab name (default: 'Stock Tracker')
            column: Column to update (default: 'L')
        
        Returns:
            Result dict with success status and message
        """
        return self.update_cell_by_identifiers(
            sheet_name=sheet_name,
            identifier_columns=['A', 'B'],  # Date in A, Stock Name in B
            identifier_values=[date, stock_name],
            target_column=column,
            new_value=note
        )
