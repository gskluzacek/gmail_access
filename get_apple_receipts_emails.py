from collections import namedtuple

from pathlib import Path
import sqlite3

from email_parsing_strategy import receipt_email_factory
from receipt import Receipt

from gmail_api import init_gmail_service, get_email_message_details, search_emails, search_email_conversations


def named_tuple_factory(cursor, row):
    # Generate a named tuple class based on the column names
    Row = namedtuple("Row", [col[0] for col in cursor.description])
    return Row(*row)


def main():
    apple_receipts = "/Users/gskluzacek/Documents/development/git_hub/gamail_access/apple_receipts_2"
    conn = sqlite3.connect('apple_receipts.sqlite')
    conn.row_factory = named_tuple_factory

    client_file = 'client_secret.json'
    service = init_gmail_service(client_file)

    query = 'from:no_reply@email.apple.com subject:("Your receipt from Apple")'

    email_messages = search_emails(service, query, max_results=200)
    for message in email_messages:
        email_detail = get_email_message_details(service, message['id'])
        if email_detail['body_type'] == 'html':
            html_body = email_detail['body']
            receipt_email_dto = receipt_email_factory(html_body)
            receipt = Receipt.from_receipt_email(receipt_email_dto)
            if not receipt.exists(conn):
                receipt.save(apple_receipts)
                receipt.insert(conn)
        else:
            print("**** not an html email ****")
            print(f"    Snippet: {email_detail['snippet']}")


if __name__ == '__main__':
    main()
