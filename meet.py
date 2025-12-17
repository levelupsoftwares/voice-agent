from __future__ import print_function

import os.path
import datetime as dt

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.apps import meet_v2


# If modifying these scopes, delete the file token.json.
# SCOPES = ['https://www.googleapis.com/auth/meetings.space.created']
SCOPES = ["https://www.googleapis.com/auth/calendar"]


def main():
    """Shows basic usage of the Google Meet API.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    try:
        # client = meet_v2.SpacesServiceClient(credentials=creds)
        # request = meet_v2.CreateSpaceRequest()
        # response = client.create_space(request=request)
        # print(f'Space created: {response.meeting_uri}')
        service = build("calendar","v3", credentials=creds)

        now =  dt.datetime.now().isoformat() + "Z"

        event_result = service.events().list(calendarId="primary", timeMin=now, maxResults=3, singleEvents=True, orderBy="startTime").execute()
        events = event_result.get("items",[])

        if not events:
            print("no upcoming events")
            return
        
        for event in events:
            start = event["start"].get("dateTime", event["start"].get("date"))
            print(start,event["summary"])


    except HttpError as error:
        # TODO(developer) - Handle errors from Meet API.
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    main()