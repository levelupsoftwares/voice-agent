from __future__ import print_function

import os.path
import datetime as dt
import uuid
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
# from google.apps import meet_v2
from pathlib import Path



BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = BASE_DIR / "credentials.json"
TOKEN_FILE = BASE_DIR / "token.json"

# If modifying these scopes, delete the file token.json.
# SCOPES = ['https://www.googleapis.com/auth/meetings.space.created']
SCOPES = ["https://www.googleapis.com/auth/calendar"]


# def main():
def get_calendar_service():
    """Shows basic usage of the Google Meet API.
        """
    creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
    if TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())


            # client = meet_v2.SpacesServiceClient(credentials=creds)
            # request = meet_v2.CreateSpaceRequest()
            # response = client.create_space(request=request)
            # print(f'Space created: {response.meeting_uri}')
    service = build("calendar","v3", credentials=creds)
    return service

        # fOR ACCESSING THE EVENTS
        # now =  dt.datetime.now().isoformat() + "Z"

        # event_result = service.events().list(calendarId="primary", timeMin=now, maxResults=3, singleEvents=True, orderBy="startTime").execute()
        # events = event_result.get("items",[])

        # if not events:
        #     print("no upcoming events")
        #     return
        
        # for event in events:
        #     start = event["start"].get("dateTime", event["start"].get("date"))
        #     print(start,event["summary"])
def eventCreate(service,summary,location,description,s_date_time,e_date_time,attendee_email):
        event = {
            "summary":summary,
            "location":location,
            "description":description,
            "colorId":6,
            "start":{
                "dateTime":s_date_time,
                # "timeZone":"Asia/Karachi"
            },
            "end":{
                "dateTime":e_date_time,
                # "timeZone":"Asia/Karachi"
            },
            "attendees":[
                {"email":f"{attendee_email}"}
            ],
            "conferenceData" : {
                "createRequest": {
                    "requestId":str(uuid.uuid4()),
                    "conferenceSolutionKey": {
                        "type": "hangoutsMeet"
                    }
                }
            }

        }
        

        try:
                event = service.events().insert(calendarId="primary", body=event, conferenceDataVersion=1).execute()
                print(f"Event created: {event.get('htmlLink')}")
        except HttpError as error:
                print(f"An error occurred: {error}")

# eventCreate("summary","location","description",19,"00:17:00","00:17:30","usmanbutt2357@gmail.com")
# if __name__ == '__main__':
#     main()
