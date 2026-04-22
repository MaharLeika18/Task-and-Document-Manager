from google_auth_oauthlib.flow import InstalledAppFlow
import os
from dotenv import load_dotenv
load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/drive"]

flow = InstalledAppFlow.from_client_secrets_file(
    os.environ.get("ALTEA_BOOKING_SYSTEM_OAUTH"),
    SCOPES,
    redirect_uri='http://localhost:5000/'
)
creds = flow.run_local_server(port=0)

with open('token.json', 'w') as token:
    token.write(creds.to_json())

print("token.json generated successfully!")