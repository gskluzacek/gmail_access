import re
from decimal import Decimal

import dateutil.parser as dap

from item_email import ItemEmail
from receipt_email import ReceiptEmail


class ParseFormat2:
    """Parse Format 1 Class.

    This class implements the EmailParsingStrategy Protocol interface. It is instantiated in the
    `get_parser` function in the `email_parsing_strategy` module as part of the logic in creating
    a `ReceiptEmail` DTO object. The EmailParsingStrategy Protocol interface is responsible for
    parsing an HTML email that contains receipt details and populating the attributes on the DTO.

    When an instance of the class is created a `BeautifulSoup` object containing the receipt email
    details is passed into the `__init__` method. And when the `parse_html_content` method is called,
    the DTO instance to be populated is passed in.
    """

    sections: list[str] = ["app store", "apple tv", "apple services"]
    category_map: dict[str, str] = {
        "app store": "app",
        "apple tv": "tv",
        "apple services": "service"
    }

    def __init__(self, soup):
        self.soup = soup
        self.receipt_email = None

    def parse_html_content(self, receipt_email: "ReceiptEmail") -> None:
        """Populates a ReceiptEmail DTO object by parsing HTML content from an emailed receipt.

        Parses and processes HTML content from the BeautifulSoup object `soup` instance
        variable. It extracts relevant receipt data. This includes details such as receipt date,
        order ID, document number, Apple account, and financial figures (subtotal, tax, total).
        Relevant fields are populated in the `receipt_email` object.

        Additionally, this method processes the items from each sections of the emailed receipt.

        :param receipt_email: An instance of ReceiptEmail to store the parsed receipt data.
        :type receipt_email: ReceiptEmail
        """
        self.receipt_email = receipt_email
        self.receipt_email.soup = self.soup

        try:
            date_str = self.get_field_value_2(r"date")
            self.receipt_email.receipt_date = dap.parse(date_str).date()
        except dap.ParserError:
            # receipt_date is defaulted to None in __init__(), so no need to do anything if the date parse fails
            pass

        # get the order id, document number and apple id account
        self.receipt_email.order_id = self.get_field_value_2(r"order id")
        self.receipt_email.doc_nbr = self.get_field_value_1(r"document no")
        apple_account = self.get_field_value_1(r"apple[\s\u00A0]account")
        if not apple_account:
            apple_account = self.get_field_value_1(r"apple id")
        self.receipt_email.apple_account = apple_account

        # process the items from each section of the emailed receipt
        for section in self.sections:
            self.process_section_items(section)

        # get the receipt subtotal, receipt tax and receipt Grand total
        self.receipt_email.subtotal = self.get_field_value_3(r"subtotal")
        self.receipt_email.tax = self.get_field_value_3(r"tax")
        self.receipt_email.total = self.get_field_value_4(r"\btotal")

    def get_field_value_1(self, field_text: str) -> str:
        """Get the string value for the corresponding `field_text`.

        Extracts the text content of a parent node containing a specific string within a 'span' tag.

        This function searches for a 'span' tag in the parsed HTML that matches the provided
        field_text. If the tag is found, it retrieves and concatenates all non-recursive text
        content of the parent node, ensuring any surrounding whitespace is stripped. If no match
        is found, it returns an empty string.

        :param field_text: The text to search for within the 'span' tag. A case-insensitive
            regular expression match is applied.
        :type field_text: str
        :return: The concatenated and stripped text content of the parent node of the found
            'span' tag. An empty string is returned if no matching tag is found.
        :rtype: str
        """
        span_tag = self.soup.find('span', string=re.compile(rf'{field_text}', re.IGNORECASE))
        if span_tag:
            return "".join(span_tag.parent.find_all(string=True, recursive=False)).strip()
        return ""

    def get_field_value_2(self, field_text: str) -> str:
        """Get the string value for the corresponding `field_text`.

        Extracts the value associated with a specified field text from a BeautifulSoup object.

        The method identifies the first 'span' tag containing the specified field text
        (case-insensitive) and locates its parent, from which it retrieves the text content of the
        second 'span' tag. If no matching field text is found, an empty string is returned.

        :param field_text: The text to search within a 'span' tag in the soup object.
        :type field_text: str
        :return: The text content of the second 'span' tag within the parent of the matched
            'span' tag, or an empty string if no match is found.
        :rtype: str
        """
        span_tag = self.soup.find('span', string=re.compile(rf'{field_text}', re.IGNORECASE))
        if span_tag:
            all_span_tags = span_tag.parent.find_all("span")
            if len(all_span_tags) < 2:
                return span_tag.parent.get_text(separator="|", strip=True).split("|")[1]
            else:
                return span_tag.parent.find_all("span")[1].text.strip()
        return ""

    def get_field_value_3(self, field_text: str) -> Decimal:
        """Get the Decimal value (dollar amount) for the corresponding `field_text`.

        Extracts and returns the numerical value associated with a specific field text.

        The method searches for a span tag within an HTML structure using the specified
        field text. If the specified span tag is found, it retrieves and processes the
        value contained in a neighboring span tag, returning it as a Decimal. If the
        field text is not found, a default value of Decimal "0.00" is returned.

        :param field_text: The text used to identify the span tag within the HTML structure.
        :type field_text: str
        :return: The numerical value associated with the field text, or "0.00" if not found.
        :rtype: Decimal
        """
        span_tag = self.soup.find('span', string=re.compile(rf'{field_text}', re.IGNORECASE))
        if span_tag:
            dollar_amt = span_tag.parent.parent.find_all("span")[1].text.strip()
            dollar_amt = dollar_amt[1:] if dollar_amt.startswith("$") else dollar_amt
            return Decimal(dollar_amt or "0.00")
        return Decimal("0.00")

    def get_field_value_4(self, field_text: str) -> Decimal:
        """Get the Decimal value (dollar amount) for the corresponding `field_text`.

        Extracts and returns a specific field's value from a parsed HTML table row based on a case-insensitive
        match for the provided field text. If the match is not found, returns a default value of 0.00.

        :param field_text: The text used to locate the corresponding HTML table row.
        :type field_text: str
        :return: The numeric value extracted from the matched row, or 0.00 if no match is found.
        :rtype: Decimal
        """
        span_tag = self.soup.find('td', string=re.compile(rf'{field_text}', re.IGNORECASE))
        if span_tag:
            dollar_amt = span_tag.parent.find_all("td")[2].text.strip()
            dollar_amt = dollar_amt[1:] if dollar_amt.startswith("$") else dollar_amt
            return Decimal(dollar_amt or "0.00")
        return Decimal("0.00")

    def get_item_details(self, section_name:str, row) -> ItemEmail:
        """Get an ItemEmail DTO for the given table row.

        Extract item details from a given row of HTML data related to a specific section.

        This method processes a row of HTML table data to extract key details such
        as the item category, descriptions, purchase amount, other amounts, and the
        associated image link. The section name is used to map the item category using
        an internally defined category map.

        :param section_name: Name of the section to determine the category mapping.
        :type section_name: str
        :param row: A BeautifulSoup object representing an HTML table row containing
            the relevant item data.
        :type row: bs4.element.Tag

        :return: An ItemEmail object that encapsulates the item details extracted
            from the HTML data, including the category, descriptions, amounts,
            and image link.
        :rtype: ItemEmail
        """
        cells = row.find_all('td')

        item_category = self.category_map[section_name]

        descriptions = cells[1].get_text(separator="|", strip=True).split("|")  # noqa
        descriptions = [desc for desc in descriptions if desc.lower() not in ("report a problem", "write a review") and desc]
        # descriptions = descriptions[:-1] if descriptions[-1].lower() == "report a problem" else descriptions

        purchase_amount = cells[2].table.tr.td.span.text.strip()
        purchase_amount = purchase_amount[1:] if purchase_amount.startswith("$") else purchase_amount
        purchase_amount = Decimal(purchase_amount or "0.00")
        other_amount = cells[3].span.text.strip()
        other_amount = other_amount[1:] if other_amount.startswith("$") else other_amount
        other_amount = Decimal(other_amount or "0.00")
        image_link = cells[0].img['src']

        return ItemEmail(item_category, descriptions, purchase_amount, other_amount, image_link)

    def process_section_items(self, section_name: str) -> None:
        """Get all items for the `section_name` section.

        Processes items within a specified section by extracting data from HTML elements
        and appending the extracted data to the corresponding list of items. This method
        searches for a section in the HTML document that matches the provided section
        name, extracts row-based details from it, processes each row, and appends the
        processed data as an item to the list.

        :param section_name: The name of the section to locate and process
        :type section_name: str
        :return: None
        :rtype: NoneType
        """
        span_tag = self.soup.find('span', string=re.compile(rf'^{section_name}$', re.IGNORECASE))
        if span_tag:
            section = span_tag.parent.parent.parent
            rows = section.find_all('tr')
            for i, row in enumerate(rows):
                if len(row.find_all(recursive=False)) > 1:
                    email_item = self.get_item_details(section_name, row)
                    self.receipt_email.items.append(email_item)
