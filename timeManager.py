from __future__ import print_function

import datetime
import os.path
import pytz 
import sqlite3

from sys import argv
from dateutil import parser
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']


def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
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
    # determine which function to run
    if argv[1] == 'add':
        duration = argv[2]
        description = argv[3]
        addEvent(creds, duration, description)
    if argv[1] == 'commit':
        commitHours(creds)


def commitHours(creds):
    try:
        service = build('calendar', 'v3', credentials=creds)

        # Call the Calendar API
        today = datetime.datetime.now(tz=pytz.timezone("Asia/Kolkata"))
        timeStart = today.isoformat()
        timeEnd = (today + datetime.timedelta(hours=23, minutes=59, seconds=59)).isoformat()  # Add 13 hours, 59 minutes, 59 seconds to get end time

        print("Getting Today's Coding Hours")
        events_result = service.events().list(calendarId='94f10758d9efe0bfa0dba240dc5bd606d012082d1d5747d87a35c430131b401b@group.calendar.google.com', 
                                            timeMin = timeStart, timeMax = timeEnd, singleEvents= True, orderBy='startTime',
                                            timeZone="Asia/Kolkata").execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
            return


        total_duration = datetime.timedelta(
            seconds=0,
            minutes =0,
            hours =0,
        )

        print("CODING HOURS:")
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))

            start_formatted = parser.isoparse(start)  # changing the start time to datetime format
            end_formatted = parser.isoparse(end) # changing the end time to datetime format
            duration = end_formatted - start_formatted
            
            total_duration += duration
            print(f"{event['summary']}, duration: {duration}")
        print(f"Total coding time: {total_duration}")

        conn = sqlite3.connect(f'hours.db')
        cur = conn.cursor()
        print("Opened database successfully")
        date = datetime.date.today()

        formatted_total_duration = total_duration.seconds/60/60
        coding_hours = (date, 'CODING', formatted_total_duration)
        cur.execute("INSERT INTO hours VALUES(?, ?, ?);", coding_hours)
        conn.commit()


    except HttpError as error:
        print('An error occurred: %s' % error)


def addEvent(creds, duration, description):
    start = datetime.datetime.utcnow()
    end = datetime.datetime.utcnow() + datetime.timedelta(hours=int(duration))
    start_formatted = start.isoformat() + 'Z'
    end_formatted = end.isoformat() + 'Z'

    event = {
        'summary': description,
        'start': {
            'dateTime': start_formatted,
            'timeZone': 'Asia/Kolkata' 
            },
        'end': {
            'dateTime': end_formatted,
            'timeZone': 'Asia/Kolkata'
        }
    }

    service = build('calendar', 'v3', credentials=creds)
    event = service.events().insert(calendarId='94f10758d9efe0bfa0dba240dc5bd606d012082d1d5747d87a35c430131b401b@group.calendar.google.com', body=event).execute()
    print('Event created: %s' % (event.get('htmlLink')))

def getHours(number_of_days):
    #get todays date
    today = datetime.date.today()
    seven_days_ago = today + datetime.timedelta(days=- int(number_of_days))

    #get hours from database
    conn = sqlite3.connect('hours.db')
    cur = conn.cursor()

    cur.execute(f"SELECT DATE, HOURS FROM hours WHERE DATE between ? AND ?", (seven_days_ago, today ))

    hours = cur.fetchall()

    total_hours = 0
    for element in hours:
        print(f"{element[0]}: {element[1]}")
        total_hours += element[1]
    print(f"Total hours: {total_hours}")
    print(f"Average hours: {total_hours/float(number_of_days)}")

if __name__ == '__main__':
    main()