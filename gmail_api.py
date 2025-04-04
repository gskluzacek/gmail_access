import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from google_apis import create_service

def init_gmail_service(client_file, api_name="gmail", api_version="v1", scopes=["https://mail.google.com/"]):
    return create_service(client_file, api_name, api_version, scopes)

def _extract_body(payload):
    body = "<Text body not available>"
    body_type = "<unknown>"
    if "parts" in payload:
        for part in payload["parts"]:
            # the intent of this code seems like there could be sub-parts in a given part ??? I cant see that being correct
            if part["mimeType"] == "multipart/alternative":
                for subpart in part["parts"]:
                    if subpart["mimeType"] == "text/plain" and "data" in subpart["body"]:
                        body = base64.urlsafe_b64decode(subpart["body"]["data"]).decode("utf-8")
                        body_type = "plain_text"
                        break
                    # TODO: should we add a check for mimeType == "text/html" and give it priority over plain text ????
            # prefer html over plain text
            elif part["mimeType"] == "text/html" and "data" in part["body"]:
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                body_type = "html"
                break
            elif part["mimeType"] == "text/plain" and "data" in part["body"]:
                body = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                body_type = "plain_text"
                break
    elif "body" in payload and "data" in payload["body"]:
        body_type = "plain_text"
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
    # TODO: not sure if there could be a case where body is in payload and payload["body"] is not plain text ???? if yes, then is the top level header or mimeType set ????
    return body, body_type

def _extract_body2(payload):
    if payload["mimeType"] != "multipart/alternative":
        raise ValueError(f"Unimplemented payload mime type: {payload['mimeType']}, you need to add more code...")

    bodies = {
        "unknown": "<Text body not available>",
    }
    for part in payload["parts"]:
        body_type = part.get("mimeType")
        if not body_type:
            raise ValueError(f"missing mime type for part: {part}")
        body = part.get("body")
        if not body:
            raise ValueError(f"missing data for part: {part}")
        data = body.get("data")
        if not data:
            raise ValueError(f"missing data for part body: {body}")
        bodies[body_type] = base64.urlsafe_b64decode(data).decode("utf-8")
    if "text/html" in bodies:
        return bodies["text/html"], "html"
    elif "text/plain" in bodies:
        return bodies["text/plain"], "plain_text"
    else:
        return bodies["unknown"], "unknown"

def get_email_messages(service, user_id="me", label_ids=None, folder_name="INBOX", max_results=5):
    messages = []
    next_page_token = None

    if folder_name:
        label_results = service.users().labels().list(userId=user_id).execute()
        labels = label_results.get("labels", [])
        folder_label_id = next((label["id"] for label in labels if label["name"].lower() == folder_name.lower()), None)
        if folder_label_id:
            if label_ids:
                label_ids.append(folder_label_id)
            else:
                label_ids = [folder_label_id]
        else:
            raise ValueError(f"Folder '{folder_name}' not found")

    while True:
        result = service.users().messages().list(
            userId=user_id,
            labelIds=label_ids,
            maxResults=min(500, max_results - len(messages)) if max_results else 500,
            pageToken=next_page_token,
        ).execute()

        messages.extend(result.get("messages", []))

        next_page_token = result.get("nextPageToken")

        if not next_page_token or (max_results and len(messages) >= max_results):
            break

    return messages[:max_results] if max_results else messages

def get_email_message_details(service, msg_id):
    message = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    payload = message["payload"]
    headers = payload.get("headers", [])

    subject = next((header["value"] for header in headers if header["name"].lower() == "subject"), None)
    if not subject:
        subject = message.get("subject", "No subject")

    sender = next((header["value"] for header in headers if header["name"] == "From"), "No sender")
    recipients = next((header["value"] for header in headers if header["name"] == "To"), "No recipients")
    snippet = message.get('snippet', 'No snippet')
    has_attachments = any(part.get('filename') for part in payload.get('parts', []) if part.get('filename'))
    date = next((header['value'] for header in headers if header['name'] == 'Date'), 'No date')
    star = message.get('labelIds', []).count('STARRED') > 0
    label = ', '.join(message.get('labelIds', []))

    body, body_type = _extract_body2(payload)

    return {
        'subject': subject,
        'sender': sender,
        'recipients': recipients,
        'body': body,
        'body_type': body_type,
        'snippet': snippet,
        'has_attachments': has_attachments,
        'date': date,
        'star': star,
        'label': label,
    }

def send_email(service, to, subject, body, body_type="plain", attachment_paths=None):
    message = MIMEMultipart()
    message["to"] = to
    message["subject"] = subject

    if body_type.lower() not in ["plain", "html"]:
        raise ValueError("body_type must be either 'plain' or 'html'")

    message.attach(MIMEText(body, body_type.lower()))

    if attachment_paths:
        for attachment_path in attachment_paths:
            if os.path.exists(attachment_path):
                filename = os.path.basename(attachment_path)

                with open(attachment_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())

                encoders.encode_base64(part)

                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {filename}",
                )

                message.attach(part)
            else:
                raise FileNotFoundError(f"File not found - {attachment_path}")

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

    sent_message = service.users().messages().send(
        userId = "me",
        body = {"raw": raw_message}
    ).execute()

    return sent_message

def download_attachments_parent(service, user_id, msg_id, target_dir):
    message = service.users().messages().get(userId=user_id, id=msg_id).execute()
    for part in message['payload']['parts']:
        if part[ 'filename']:
            att_id = part['body']['attachmentId']
            att = service.users().messages().attachments().get(userId=user_id, messageId=msg_id, id=att_id).execute()
            data = att['data']
            file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
            file_path = os.path.join(target_dir, part['filename'])
            print('Saving attachment to: ', file_path)
            with open(file_path, 'wb') as f:
                f.write(file_data)

def download_attachments_all(service, user_id, msg_id, target_dir):
    thread = service.users().threads().get(userId=user_id, id=msg_id).execute()
    for message in thread ['messages']:
        for part in message['payload']['parts']:
            if part[ 'filename']:
                att_id = part['body']['attachmentId']
                att = service.users().messages().attachments().get(userId=user_id, messageId=message['id'], id=att_id).execute()
                data = att['data']
                file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
                file_path = os.path.join(target_dir, part['filename'])
                print('Saving attachment to: ', file_path)
                with open(file_path, 'wb') as f:
                    f. write(file_data)

def search_emails(service, query, user_id='me', max_results=5):
    messages = []
    next_page_token = None

    while True:
        result = service.users().messages().list(
            userId=user_id,
            q=query,
            maxResults=min(500, max_results - len(messages)) if max_results else 500,
            pageToken=next_page_token
        ).execute()

        messages.extend(result.get('messages', []))

        next_page_token = result.get('nextPageToken')

        if not next_page_token or (max_results and len(messages) >= max_results):
            break

    return messages[:max_results] if max_results else messages

def search_email_conversations(service, query, user_id='me', max_results=5):
    conversations = []
    next_page_token = None

    while True:
        result = service.users().threads().list(
            userId=user_id,
            q=query,
            maxResults=min(500, max_results - len(conversations)) if max_results else 500, pageToken=next_page_token
        ).execute()

        conversations.extend(result.get('threads', []))

        next_page_token = result.get('nextPageToken')

        if not next_page_token or (max_results and len(conversations) >= max_results) :
            break

    return conversations[:max_results] if max_results else conversations
