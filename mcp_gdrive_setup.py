import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import pickle
import json

class MCPGdriveSetup:
    def __init__(self, credentials_path):
        self.SCOPES = ['https://www.googleapis.com/auth/drive.file']
        self.credentials_path = credentials_path
        self.token_path = os.path.join(os.path.dirname(credentials_path), 'token.pickle')
        self.creds = None
        
    def authenticate(self):
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                self.creds = pickle.load(token)
                
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(f'Credentials file not found at {self.credentials_path}')
                    
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES)
                self.creds = flow.run_local_server(port=0)
                
            with open(self.token_path, 'wb') as token:
                pickle.dump(self.creds, token)
        
        return build('drive', 'v3', credentials=self.creds)
        
    def create_folder(self, service, folder_name, parent_id=None):
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        file = service.files().create(body=file_metadata, fields='id').execute()
        return file.get('id')
        
    def setup_mcp_folders(self):
        service = self.authenticate()
        
        # Create main folder
        mcp_folder_id = self.create_folder(service, 'MCP_Server')
        
        # Create subfolders
        subfolders = ['backups', 'logs', 'configs']
        folder_ids = {}
        
        for folder in subfolders:
            folder_ids[folder] = self.create_folder(service, folder, mcp_folder_id)
            
        # Save folder IDs to config file
        config = {
            'main_folder': mcp_folder_id,
            'subfolders': folder_ids
        }
        
        config_path = os.path.join(os.path.dirname(self.credentials_path), 'gdrive_config.json')
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
            
        return mcp_folder_id, folder_ids

def main():
    # Get the script's directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Set credentials path
    credentials_path = os.path.join(script_dir, 'credentials.json')
    
    # Check if credentials file exists
    if not os.path.exists(credentials_path):
        print(f'Error: credentials.json not found in {script_dir}')
        print('Please place your Google Drive API credentials file in the same directory as this script.')
        return
    
    try:
        # Run setup
        gdrive_setup = MCPGdriveSetup(credentials_path)
        main_folder_id, subfolder_ids = gdrive_setup.setup_mcp_folders()
        
        print('\nGoogle Drive setup completed successfully!')
        print(f'Main folder ID: {main_folder_id}')
        print('\nSubfolder IDs:')
        for folder, folder_id in subfolder_ids.items():
            print(f'{folder}: {folder_id}')
            
        print('\nConfiguration has been saved to gdrive_config.json')
        
    except Exception as e:
        print(f'\nError during setup: {str(e)}')

if __name__ == '__main__':
    main()