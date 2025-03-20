from gmail_api import init_gmail_service, get_email_messages, get_email_message_details


def main():
    client_file = 'client_secret.json'
    service = init_gmail_service(client_file)
    messages = get_email_messages(service, max_results=2000)

    for msg in messages:
        details = get_email_message_details(service, msg['id'])
        if details:
            if details["sender"].startswith("Chase") and details["subject"].startswith("You received money with Zelle"):
                print(f"From: {details['sender']}")
                print(f"Subject: {details['subject']}")
                print(f"Date: {details['date']}")
                print(f"Snippet: {details['snippet']}")
                # print(f"Recipients: {details['recipients']}")
                # print(f"Has Attachments: {details['has_attachments']}")
                # print(f"Star: {details['star']}")
                # print(f"Label: {details['label']}")
                # print("-" * 50)
                # print(f"Body:\n{details['body']}\n")  # Print first 100 characters of the body
                print("=" * 50)

if __name__ == '__main__':
    main()
