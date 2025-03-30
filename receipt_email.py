from datetime import date
from decimal import Decimal

from bs4 import BeautifulSoup

from item_email import ItemEmail


class ReceiptEmail:
    """Email Receipt Data Transfer Object (DTO).

    Represents an email containing structured data related to an order, parsed using a specific
    email parsing strategy. The purpose of this class is to store all relevant information extracted
    with the parser for additional processing.

    Unless otherwise noted, all instance variables are defaulted to None before parsing.

    :ivar soup: beautiful soup object with the parsed html content.
    :type soup: BeautifulSoup | None
    :ivar receipt_date: The date when the receipt was issued.
    :type receipt_date: date | None
    :ivar order_id: The unique identifier for the order.
    :type order_id: str | None
    :ivar doc_nbr: The document number associated with the receipt.
    :type doc_nbr: str | None
    :ivar apple_account: The Apple account associated with the receipt.
    :type apple_account: str | None
    :ivar subtotal: The subtotal amount of the receipt.
    :type subtotal: Decimal | None
    :ivar tax: The tax amount listed on the receipt.
    :type tax: Decimal | None
    :ivar card: The payment card information (e.g., last four digits) used for the purchase.
    :type card: str | None
    :ivar total: The total amount of the transaction listed on the receipt.
    :type total: Decimal | None
    :ivar items: A list of ItemEmail objects that represents the individual items on the receipt. Defaults to an empty list before parsing.
    :type items: list[ItemEmail]
    """
    def __init__(self):
        """Facilitates parsing an HTML email receipt into its corresponding DTO.

        An instance object that implements the `EmailParsingStrategy` interface must be passed in
        to the constructor. Typically, the constructor will not be called directly, but rather
        called by the `receipt_email_factory` method.
        """
        self.soup: BeautifulSoup | None = None
        self.receipt_date: date | None  = None
        self.order_id: str | None = None
        self.doc_nbr: str | None = None
        self.apple_account: str | None = None
        self.subtotal: Decimal | None = None
        self.tax: Decimal | None = None
        self.card: str | None = None
        self.total: Decimal | None = None

        self.items: list[ItemEmail] = []
