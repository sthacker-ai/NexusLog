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
from config import get_env


class SheetsIntegration:
    """Google Sheets integration for content ideas"""
    
    def __init__(self):
        self.credentials_path = get_env('GOOGLE_SHEETS_CREDENTIALS_PATH')
        self.sheet_id = get_env('GOOGLE_SHEET_ID')
        
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
                           identifier_values: List[str], data_range: str = None, 
                           reverse: bool = False, sheet_id: str = None) -> int:
        """
        Find a row by matching values in multiple columns.
        Supports reverse search and custom sheet ID.
        """
        try:
            active_sheet_id = sheet_id or self.sheet_id
            
            # Determine search range
            if data_range:
                search_range = f"'{sheet_name}'!{data_range}"
            else:
                search_range = f"'{sheet_name}'!A:Z"
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=active_sheet_id,
                range=search_range
            ).execute()
            
            values = result.get('values', [])
            
            if not values:
                return -1
            
            # Convert column letters to indices (A=0, B=1, etc.)
            col_indices = [ord(col.upper()) - ord('A') for col in identifier_columns]
            
            # Create iterator (forward or reverse)
            rows_iter = enumerate(values)
            if reverse:
                rows_iter = reversed(list(enumerate(values)))
            
            # Search each row
            for row_idx, row in rows_iter:
                # Check if all identifier values match
                matches = True
                for idx_in_identifiers, col_idx in enumerate(col_indices):
                    if col_idx >= len(row):
                        matches = False
                        break
                    
                    expected_value = identifier_values[idx_in_identifiers]
                    val = str(row[col_idx]).strip().lower()
                    exp = str(expected_value).strip().lower()
                    
                    # Date comparison might need more robustness, but exacting string match is safest for now
                    if val != exp:
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

    def log_trade_journal(self, date: str, stock_symbol: str, commentary: str = None, 
                         lessons: str = None) -> Dict:
        """
        Log entry to the Trading Journal.
        sheet_id: 1dNB-i8GoYDR4upLYN-swX6G2wZn1rCnEE7SDnRf1BP8
        """
        TRADING_SHEET_ID = '1dNB-i8GoYDR4upLYN-swX6G2wZn1rCnEE7SDnRf1BP8'
        SHEET_NAME = "Journal"
        
        # 1. Find the row (Reverse chronological)
        row_num = self.find_row_by_values(
            sheet_name=SHEET_NAME,
            identifier_columns=['A', 'B'], # Date=A, Ticker=B
            identifier_values=[date, stock_symbol],
            reverse=True,
            sheet_id=TRADING_SHEET_ID
        )
        
        if row_num == -1:
            return {'success': False, 'message': f"❌ Error: No matching trade found for {stock_symbol} on {date}. Checking 'Journal' tab."}
        
        # 2. Update Columns L and M
        updates = []
        if commentary:
            updates.append({'col': 'L', 'val': commentary})
        if lessons:
            updates.append({'col': 'M', 'val': lessons})
            
        messages = []
        for up in updates:
            cell_ref = f"'{SHEET_NAME}'!{up['col']}{row_num}"
            try:
                self.service.spreadsheets().values().update(
                    spreadsheetId=TRADING_SHEET_ID,
                    range=cell_ref,
                    valueInputOption='USER_ENTERED',
                    body={'values': [[up['val']]]}
                ).execute()
                messages.append(f"Updated {up['col']}")
            except Exception as e:
                messages.append(f"Failed {up['col']}: {str(e)}")
                
        return {'success': True, 'message': f"Log updated for {stock_symbol} (Row {row_num}): {', '.join(messages)}"}
