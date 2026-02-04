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
