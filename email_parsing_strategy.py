from typing import Protocol

from bs4 import BeautifulSoup

from parse_format_1 import ParseFormat1
from parse_format_2 import ParseFormat2

from receipt_email import ReceiptEmail

# Constant for readability
PARSE_FMT_1_IND = "receipt"


class EmailParsingStrategy(Protocol):
    """An interface for email parsing strategies.

    This class defines the protocol that any email parsing strategy class
    should follow. It serves as a blueprint for implementing parsing schemes
    for extracting relevant information from email HTML content. The purpose
    of this class is to provide a standardized mechanism to parse and analyze
    the HTML of a receipt email using BeautifulSoup and other tools. Classes
    implementing this protocol can define their own parsing logic while
    adhering to the defined structure.

    :ivar soup: the BeautifulSoup instance object containing HTML content of the receipt email.
    :type soup: BeautifulSoup
    """

    soup: BeautifulSoup

    def parse_html_content(self, receipt_email: "ReceiptEmail") -> None:
        """Parses the HTML content of an email receipt.

        This method is designed to handle the extraction of relevant data from
        received email receipt content in HTML format. It performs parsing operations,
        identifies specific elements from the HTML structure, and processes the data
        appropriately for further usage.

        :param receipt_email: The "empty" email receipt DTO instance that will be populated by this method.
        :type receipt_email: ReceiptEmail
        """
        ...


def get_parser(soup: BeautifulSoup) -> EmailParsingStrategy:
    """Determine the parsing strategy to use in parsing the HTML email receipt..

    Determines the appropriate parsing strategy based on the HTML content structure.
    :param soup: BeautifulSoup object representing the parsed HTML.
    :return: An instance of EmailParsingStrategy.
    """
    top_divs = soup.div.find_all("div", recursive=False)
    if top_divs and top_divs[0].text.strip().lower() == PARSE_FMT_1_IND:
        return ParseFormat1(soup)
    else:
        return ParseFormat2(soup)


def receipt_email_factory(html_content: str) -> ReceiptEmail:
    """Creates a populated instance of the ReceiptEmail DTO.

    Creates an instance of ReceiptEmail by determining the parsing format from
    the given HTML content. It uses BeautifulSoup to parse the content and decides
    the format based on the structure and content of the provided HTML. If the
    top-level child div contains the text "receipt", format 1 parsing is used;
    otherwise, format 2 parsing is employed.

    :param html_content: an HTML string that represents the email receipt to parse.
    :type html_content: str
    :return: An instance of ReceiptEmail created based on the parsed HTML content.
    :rtype: Self
    """
    soup = BeautifulSoup(html_content, "html.parser")
    parser = get_parser(soup)
    receipt_email = ReceiptEmail()
    parser.parse_html_content(receipt_email)

    return receipt_email
