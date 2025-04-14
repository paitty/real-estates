from playwright.sync_api import sync_playwright

import os.path
import time
import random
list1 = [2, 3, 4, 5, 6, 7]
import asyncio

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# The ID and range of a sample spreadsheet.
SAMPLE_SPREADSHEET_ID = "1SPmb90afxgQ2kDXYqLIUzyOd0LwbeOFvsd0WeD3bklc"
SAMPLE_RANGE_NAME = "Sheet1!A2:A"
SAMPLE_RANGE_NAME2 = "Sheet1!C2:F"

def get_numbers_from_njuskalo(just_link):
    output = []
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=False)
        page = browser.new_page()
        page.goto("https://www.njuskalo.hr/prodaja-kuca/istra")
        page.click('button:has-text("Prihvati i zatvori")')
        #page.click('button:has-text("RAZUMIJEM")')
        for link in just_link:
            number = 0
            time.sleep(1+random.choice(list1))
            page.goto(link[0])
            page.mouse.wheel(0, 1500)
            price =''
            title = ''
            location = ''
            contact = ''
            all_items = page.locator("dd").all()
            for item in all_items:
                if item.get_attribute("class")=='ClassifiedDetailSummary-priceDomestic':
                    price = item.inner_html().strip().replace("&nbsp;", " ")
            
            all_items = page.locator("h1").all()
            for item in all_items:
                if item.get_attribute("class")=='ClassifiedDetailSummary-title':
                    title = item.inner_html().strip()
               
            all_items = page.locator("span").all()
            tip=0
            for item in all_items:
                if item.get_attribute("class")=='ClassifiedDetailBasicDetails-textWrapContainer':
                  location = item.inner_html().strip()
                  tip=tip+1
                  if tip == 2:
                    break
     
            all_items = page.locator("a").all()
            for item in all_items:
                if item.get_attribute("class")=='ClassifiedDetailOwnerDetails-contactEntryLink link-standard link-breakable ':
                    contact = item.inner_html().strip()

            output.append([title, price,location, contact])
        browser.close()
    return output

def main():
  """Shows basic usage of the Sheets API.
  Prints values from a sample spreadsheet.
  """
  creds = None
  # The file token.json stores the user's access and refresh tokens, and is
  # created automatically when the authorization flow completes for the first
  # time.
  if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
  # If there are no (valid) credentials available, let the user log in.
  if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
      creds.refresh(Request())
    else:
      flow = InstalledAppFlow.from_client_secrets_file(
          "credentials.json", SCOPES
      )
      creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open("token.json", "w") as token:
      token.write(creds.to_json())

  try:
    service = build("sheets", "v4", credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    
    result = (
        sheet.values()
        .get(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME)
        .execute()
    )
    values = result.get("values", [])
    
    
    just_link = values
    values = [
        get_numbers_from_njuskalo(just_link),
    ]
    Body = {
    'values' : values[0],
    }
    result1 = (sheet.values()
              .update(spreadsheetId=SAMPLE_SPREADSHEET_ID, range=SAMPLE_RANGE_NAME2,valueInputOption='RAW', body=Body)
              .execute()
    )



  except HttpError as err:
    print(err)


if __name__ == "__main__":
  main()