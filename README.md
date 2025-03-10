Clone this repo
edit the .env.docker file
run `docker-compose up`


Example .env.docker file you need:
```
# FILL THESE OUT
JIRA_EMAIL = "JIRA_EMAIL" #replace with jira email
JIRA_API_TOKEN = "JIRA_API_TOKEN" #replace with jira api token
RECEIVER_EMAIL = "RECEIVER EMAIL" # replace with the email u want to receive

JIRA_URL = "https://ORG_DOMAIN.atlassian.net"
JIRA_BOARD_ID = "BOARD_ID"
SMTP_SERVER = "smtp.gmail.com"  # Or your SMTP server
SMTP_PORT = 465  # For SSL
SENDER_EMAIL = "YOUR_SMTP_EMAIL"  # Or your own SMTP email if u want
SENDER_PASSWORD = "YOUR_SMTP_PW"  # Or your own SMTP PW if u want
```
