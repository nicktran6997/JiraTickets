import base64
import json
import httpx
from dotenv import load_dotenv
import os


import smtplib
import ssl

from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

load_dotenv()

#Define all needed env variables here
JIRA_URL = os.getenv("JIRA_URL")
EMAIL = os.getenv("JIRA_EMAIL")
API_TOKEN = os.getenv("JIRA_API_TOKEN")
BOARD_ID = os.getenv("JIRA_BOARD_ID")

SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SENDER_EMAIL = os.getenv("SENDER_EMAIL") 
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD") 

RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

auth_string = f"{EMAIL}:{API_TOKEN}"
auth_bytes = auth_string.encode("ascii")
auth_base64 = base64.b64encode(auth_bytes).decode("ascii")

headers = {
    "Authorization": f"Basic {auth_base64}",
    "Content-Type": "application/json",
}

sprint_names = []

def callout_to_api(url, method, payload=None):
    with httpx.Client() as client:
        if method == 'GET':
            return client.get(url, headers=headers)
        elif method == 'POST':
            return client.post(url, headers=headers, json=payload)
        else:
            return None # Handle other methods if needed

def get_all_active_sprints():
    sprint_ids = []
    sprint_url = f"{JIRA_URL}/rest/agile/1.0/board/{BOARD_ID}/sprint?state=active"
    sprint_response = callout_to_api(sprint_url, 'GET')
    if sprint_response.status_code != 200:
        print(f"Error getting active sprints: {sprint_response.status_code}, {sprint_response.text}")
        return "" # return empty string, not empty list.
    sprint_data = sprint_response.json()
    for curr_sprint in sprint_data["values"]:
        sprint_ids.append(curr_sprint["id"])
        sprint_names.append(curr_sprint["name"])
        print(f'sprint_id: {curr_sprint["id"]}')
    return ",".join(map(str, sprint_ids))

def find_users_issues():
    sprint_ids = get_all_active_sprints()
    if not sprint_ids: #check if sprint_ids is empty string.
        print("No active sprints found.")
        return

    payload = {
        "jql": f"sprint IN ({sprint_ids}) AND (assignee = currentUser() OR cf[10181] = currentUser())",
        "fields": ["key", "summary", "status", "assignee", "priority", "reporter", "customfield_10181"],
    }
    search_url = f"{JIRA_URL}/rest/api/3/search"
    search_response = callout_to_api(search_url, 'POST', payload)

    if search_response.status_code != 200:
        print(f"Error searching issues: {search_response.status_code}, {search_response.text}")
        return

    issues_data = search_response.json()
    return process_issues(issues_data["issues"])
    #save_json_list_to_file(issues_data, 'issues.json')

def save_json_list_to_file(json_list, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_list, f, ensure_ascii=False, indent=4)
        print(f"JSON data successfully saved to {filename}")
    except Exception as e:
        print(f"Error saving JSON data to {filename}: {e}")

def is_in_review(issue):
    if issue['fields']['customfield_10181'] is None:
        return False
    return issue['fields']['customfield_10181']['emailAddress'] == EMAIL and issue['fields']['status']['name'] == 'Review'

def is_in_my_review(issue):
    return is_in_review(issue) and issue['fields']['assignee']['emailAddress'] == EMAIL

def is_in_another_code_review(issue):
    return is_in_review(issue) and issue['fields']['assignee']['emailAddress'] != EMAIL

def process_issues(issues):
    issues_map = {
        "In my review": [],
        "In another code review": [],
        "In Progress": [],
        "In QA": [],
        "Completed": [],
        "Blocked": []
    }
    for issue in issues:
        markdown_text = create_markdown(issue)
        issue_list = []
        status_name = issue['fields']['status']['name']
        if is_in_my_review(issue):
            issue_list = issues_map["In my review"]
        elif is_in_another_code_review(issue):
            issue_list = issues_map["In another code review"]
        elif status_name == 'In Progress' or status_name == 'Parking Lot':
            issue_list = issues_map["In Progress"]
        elif in_qa_testing(issue):
            issue_list = issues_map["In QA"]
        elif status_name == 'Ready To Merge' or status_name == 'Merged':
            issue_list = issues_map["Completed"]
        elif blocked(issue):
            issue_list = issues_map["Blocked"]
        else:
            print(f'unknown status for issue: {status_name}')
            print(issue['fields']['summary'])
            continue
        issue_list.append(markdown_text)
    write_to_txt(issues_map, "tickets.txt")
    print("finished processing tickets")

def create_ticket_url(ticket_key):
    return f"{JIRA_URL}/browse/{ticket_key}"

def in_qa_testing(issue):
    if issue['fields']['customfield_10181'] is None:
        return False
    return issue['fields']['status']['name'] == 'Testing' and issue['fields']['customfield_10181']['emailAddress'] == EMAIL

def blocked(issue):
    return issue['fields']['status']['name'] == 'Blocked' and issue['fields']['assignee']['emailAddress'] == EMAIL

def create_markdown(issue):
    return f"[{issue['fields']['summary']}]({create_ticket_url(issue['key'])})"

def write_to_txt(json, filename):
    delimiter = "*" * 20
    with open(filename, 'w') as f:
        for key in json.keys():
            f.write(f"{delimiter} {key} {delimiter}\n")
            for issue in json[key]:
                f.write(issue + "\n")



def get_reviewed_prs():
    #/repos/leandata/{repo}/pulls/{pull_number}/reviews

    return

def find_reviewed_tickets():
    # 1) Query reviewed github PRs in the past 2 weeks
    # 2) Find the Ticket numbers from reviewed PRs
    # 3) Query Jira API with those ticket numbers that are also part of this sprint.
    return

def send_email_with_attachment():
    """
    Sends an email with an attachment based on data from a JSON string.

    Args:
        smtp_server (str): SMTP server address.
        port (int): SMTP server port.
        sender_email (str): Sender's email address.
        sender_password (str): Sender's email password.
    """
    try:

        subject = "Sprint Planning Tickets"
        body = "Here you go boss, for sprints: " + str(sprint_names)
        attachment_path = "./tickets.txt"

        message = MIMEMultipart()
        message["From"] = SENDER_EMAIL
        message["To"] = RECEIVER_EMAIL
        message["Subject"] = subject

        message.attach(MIMEText(body, "plain"))

        with open(attachment_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())

        encoders.encode_base64(part)

        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {attachment_path.split('/')[-1]}", # Get filename
        )

        message.attach(part)

        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, message.as_string())

        print("Email sent successfully!")

    except json.JSONDecodeError:
        print("Error: Invalid JSON format.")
    except ValueError as e:
        print(f"Error: {e}")
    except FileNotFoundError:
        print(f"Error: Attachment file not found at {attachment_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

find_users_issues()


send_email_with_attachment()
