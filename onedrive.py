import requests
import os

# Replace these with your actual values
client_id = '6a83299a-f5fa-421e-9f5b-b54350ce6c7f'
client_secret = 'Hmz8Q~Ym1Vw_ooKmtizZfANWxiPiGhsXSnax0cf8'
tenant_id = 'b6041961-ec10-49e5-824e-cdd0f1f98cad'
username = os.environ.get("M365_ADMIN_EMAIL")
password = os.environ.get("M365_ADMIN_PASSWORD")
folder_id = 'approot:'  # You need to find the folder ID from your OneDrive

print(username)
print(password)
print(tenant_id)

# Get an access token using the client credentials flow
token_url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
token_data = {
    'grant_type': 'password',
    'client_id': client_id,
    'client_secret': client_secret,
    'scope': 'https://graph.microsoft.com/.default',
    'username': username,
    'password': password
}

token_response = requests.post(token_url, data=token_data).json()
access_token = token_response.get('access_token')

if not access_token:
    print("Authentication failed.")
    exit()

# Get folder information
folder_url = f'https://graph.microsoft.com/v1.0/me/drive/items/{folder_id}'
headers = {
    'Authorization': f'Bearer {access_token}'
}

folder_info_response = requests.get(folder_url, headers=headers).json()
print(folder_info_response)
total_size = folder_info_response.get('size')

if total_size:
    print(f'Total size of the folder: {total_size} bytes')
else:
    print('Unable to retrieve folder size.')