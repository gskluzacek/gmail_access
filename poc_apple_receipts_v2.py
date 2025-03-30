from collections import namedtuple

from pathlib import Path
import sqlite3

from email_parsing_strategy import receipt_email_factory
from receipt import Receipt


def named_tuple_factory(cursor, row):
    # Generate a named tuple class based on the column names
    Row = namedtuple("Row", [col[0] for col in cursor.description])
    return Row(*row)


def main():
    conn = sqlite3.connect('apple_receipts.sqlite')
    conn.row_factory = named_tuple_factory

    dir_path = Path("/Users/gskluzacek/Documents/development/git_hub/gamail_access/apple_receipts_1")
    filenames = sorted(dir_path.glob("*.html"))
    # filenames = ['/Users/gskluzacek/Documents/development/git_hub/gamail_access/apple_receipts_1/20250212154504_html.html']

    receipts = []
    for filename in filenames:
        with open(filename, 'r') as f:
            html_content = f.read()
        receipt_email_dto = receipt_email_factory(html_content)

        receipt = Receipt.from_receipt_email(receipt_email_dto)
        receipts.append(receipt)

    print("-" * 200)
    for receipt in receipts:
        if not receipt.exists(conn):
            receipt.insert(conn)
        # all_descs = " | ".join([f"[{item.item_type.value}] {item.description_1} // {item.description_2 or ""}" for item in receipt.items])
        # print(f"date: {receipt.receipt_date}   order:{receipt.order_id}   user: {receipt.apple_account:<25} order total: ${receipt.total:>6}    >>>> {all_descs}")

    conn.close()

if __name__ == '__main__':
    main()
