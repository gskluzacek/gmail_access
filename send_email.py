from pathlib import Path
from gmail_api import init_gmail_service, send_email, download_attachments_parent, download_attachments_all


def main():
    client_file = "client_secret.json"
    service = init_gmail_service(client_file)
    msg_id = send_mail(service)
    get_mail_with_attachments(service, msg_id)

def get_mail_with_attachments(service, msg_id):
    user_id = 'me'
    download_dir = Path('./downloads')
    download_attachments_parent(service, user_id, msg_id, download_dir)

def send_mail(service):
    to_address = "gskluzacek@gmail.com"
    email_subject = "email with attachments"
    email_body = "I am sending this email via the google API.\nIts intent is to test the downloading of attachments."
    attachment_dir = Path("./attachments")
    attachment_files = list(attachment_dir.glob("*"))
    response_email_sent = send_email(
        service,
        to_address,
        email_subject,
        email_body,
        body_type='plain',
        attachment_paths=attachment_files,
    )
    print(response_email_sent)
    return response_email_sent["id"]


if __name__ == "__main__":
    main()
