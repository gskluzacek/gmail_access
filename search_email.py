#
# documentation on the search operators
# https://support.google.com/mail/answer/7190?hl=en&ref_topic=3394593&sjid=13343962876120662756-NC
#
from datetime import datetime

from bs4 import BeautifulSoup

from gmail_api import init_gmail_service, get_email_message_details, search_emails, search_email_conversations


def main():
    apple_receipts = "/Users/gskluzacek/Documents/development/git_hub/gamail_access/apple_receipts_1"
    # Create the Gmail API service
    client_file = 'client_secret.json'
    service = init_gmail_service(client_file)

    # to check for zelle activity
    # query = 'from:chase subject:("You received money with Zelle")'

    # to check for apple activity
    query = 'from:no_reply@email.apple.com subject:("Your receipt from Apple")'

    email_messages = search_emails(service, query, max_results=200)
    for message in email_messages:
        email_detail = get_email_message_details(service, message['id'])
        # print(message['id'])
        # print(f"Subject: {email_detail['subject']}")
        print(f"Date: {email_detail['date']}")
        date_obj = datetime.strptime(email_detail['date'], "%a, %d %b %Y %H:%M:%S %z (%Z)")
        date_str = date_obj.strftime("%Y%m%d%H%M%S")
        # print(f"Label: {email_detail['label']}")
        print(f"Snippet: {email_detail['snippet']}")
        if email_detail['body_type'] == 'plain_text':
            print("plain text body")
            filename = f"{apple_receipts}/{date_str}_plain_text.txt"
            with open(filename, 'w') as f:
                f.write(email_detail['body'])
            # print(f"Body: {email_detail['body'][:500]}")
        elif email_detail['body_type'] == 'html':
            print("html body")
            soup = BeautifulSoup(email_detail['body'], 'html.parser')
            filename1 = f"{apple_receipts}/{date_str}_html_text.txt"
            filename2 = f"{apple_receipts}/{date_str}_html.html"
            html_text = soup.get_text(separator='\n', strip=True)
            with open(filename1, 'w') as f:
                f.write(html_text)
            pretty_html = soup.prettify()
            with open(filename2, 'w') as f:
                f.write(pretty_html)
            print("<< unknown body type >>")
        else:
            print('-' * 50)

"""
subjects:
Your receipt from Apple.
Your recent purchase with your Apple ID.
Subscription Confirmation
Your Subscription Confirmation
Your Subscription is Expiring
Your Subscription Price Increase
"""


if __name__ == '__main__':
    main()
