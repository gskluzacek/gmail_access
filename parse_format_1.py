from datetime import date
from decimal import Decimal

import dateutil.parser as dap

from item_email import ItemEmail
from receipt_email import ReceiptEmail


class ParseFormat1:
    """Parse Format 1 Class.

    This class implements the EmailParsingStrategy Protocol interface. It is instantiated in the
    `get_parser` function in the `email_parsing_strategy` module as part of the logic in creating
    a `ReceiptEmail` DTO object. The EmailParsingStrategy Protocol interface is responsible for
    parsing an HTML email that contains receipt details and populating the attributes on the DTO.

    When an instance of the class is created a `BeautifulSoup` object containing the receipt email
    details is passed into the `__init__` method. And when the `parse_html_content` method is called,
    the DTO instance to be populated is passed in.
    """

    # field name to attribute name mapping section 1
    FIELD_ATTR_SECTION_1 = {
        "order id": "order_id",
        "document": "doc_nbr",
        "apple account": "apple_account",
    }

    # field name to attribute name mapping section 3
    FIELD_ATTR_SECTION_3 = {
        "subtotal": "subtotal",
        "tax": "tax",
    }

    def __init__(self, soup):
        """Initializes a ParseFormat1 instance.

        Initializes an instance of the parser to extract specific details from the provided BeautifulSoup
        object which contains HTML receipt email.

        :param soup: A BeautifulSoup object that contains the parsed HTML or XML document to be processed.
        :type soup: BeautifulSoup
        """
        self.soup = soup
        self.receipt_email = None

    def parse_html_content(self, receipt_email: "ReceiptEmail") -> None:
        """Populates a ReceiptEmail DTO object by parsing HTML content from an emailed receipt.

        Parses and processes HTML content from the BeautifulSoup object `soup` instance
        variable. The method extracts top-level `div` tags from the HTML, identifies specific
        sections, and processes each section accordingly.

        The content is divided into three sections, and they are processed using corresponding
        helper methods for each section.

        :param receipt_email: The "empty" email receipt DTO instance that will be populated by this method.
        :type receipt_email: ReceiptEmail
        """
        self.receipt_email = receipt_email

        sections = self.get_sections()
        self.process_section_1(sections[0])
        self.process_section_2(sections[1])
        self.process_section_3(sections[2])

    def get_sections(self):
        """Extract specific child sections from an HTML structure.

        This method filters and retrieves specific child elements from the parsed
        HTML tree. It identifies the second top-level child div and extracts all
        direct children that match specific tags ('div', 'table'), while ignoring
        nested levels.

        :return: List of extracted child elements matching the specified tags
                 within the second top-level div.
        :rtype: list
        """
        top_level_child_divs = self.soup.div.find_all("div", recursive=False)
        return top_level_child_divs[1].find_all(("div", "table"), recursive=False)

    def process_section_1(self, section):
        """Parses section 1 of the HTML document containing receipt details.

        This function extracts data from a `<p>` tag for the receipt date, and pairs of `<p>`
        tags within `<div>` tags for other receipt-related fields. The extracted data is used to
        populate attributes of the `receipt_email` DTO which is stored as an attribute on this
        class instance.

        :param section: The HTML section represented by a BeautifulSoup Tag object to be processed.
        :type section: bs4.element.Tag
        :raises ValueError: Raised if a field name in the `<div>` tags does not match predefined mapping.
        """
        # SECTION #1 - <div> tag
        # the 1st section contains: a <p> tag, followed by multiple <div> tags

        # first, we get the text from the <p> tag which contains the receipt date without a label
        self.receipt_email.receipt_date = self.parse_date(section.p.text)

        fields_names_values = self.parse_sect_1_fields(section)
        self.set_sect_1_attribs(fields_names_values)


    def process_section_2(self, section):
        """Parses section 2 of the HTML document containing receipt details.

        Processes the second section of an HTML receipt email to extract information
        about purchased items, including their descriptions, purchase amount, and
        associated image link.

        The section is assumed to contain a table (`<table>` tag) with one or more rows,
        each row comprising three cells:
        1. An image link related to the purchased item.
        2. A description paragraph (`<p>` tags) of the purchased item.
        3. The purchase amount before taxes.

        The method parses the content of each cell to extract and transform the desired
        information, then creates and appends an EmailItem object the list of items for the receipt email
        DTO which is stored as an attribute on this class instance.

        :param section: An HTML section tag containing the table from which purchase
            information will be extracted.
        :type section: bs4.element.Tag
        """
        # SECTION #2 - <table> tag
        # the 2nd section contains a table with 1 row that has 3 cells

        # perhaps there could be multiple rows, each with 1 item ???? so far, have only seen
        # receipts with just 1 item

        # 1. the 1st cell contains the image link for the item purchased
        # 2. the 2nd cell contains multiple <p> tags which provide description details on the purchase
        # 3. the 3rd cell contains the purchase amount (before taxes)

        section_2_td_tags = section.find_all("td")

        image_link = section_2_td_tags[0].img['src']
        descriptions = section_2_td_tags[1].get_text(strip=True, separator="|").split("|")  # NOQA
        descriptions = descriptions[:-1] if descriptions[-1].lower() == "report a problem" else descriptions
        purchase_amount = self.parse_decimal(section_2_td_tags[2].text.strip())

        self.receipt_email.items.append(ItemEmail(
            item_category=None,
            descriptions=descriptions,
            purchase_amount=purchase_amount,
            other_amount=None,
            image_link=image_link,
        ))

    def process_section_3(self, section):
        """Parses section 3 of the HTML document containing receipt details.

        Processes the third section of an HTML email, which contains billing and payment-related
        information. In this section, multiple levels of nested HTML tags are handled to extract
        specific financial details such as subtotal, tax, total, and the payment card used for
        the transaction. The extracted values are assigned to corresponding attributes of the
        `receipt_email` DTO which is stored as an attribute on this class instance.

        :param section: The HTML section containing the billing and payment details to be processed.
        :type section: bs4.element.Tag
        :raises ValueError: Raised when a field name in the subtotal and tax information is not
                            recognized or is missing from the defined mapping.
        """
        # SECTION #3  - <div> tag
        # the 3rd sections, contains a <p> tag followed by a <div> tag,
        #
        # we ignore <p> tag and just use the <div> tag, which itself contains 2 child <div> tags
        # 1. the 1st child <div> tag contains the billing address details, which we do not need
        # 2. the 2nd child <div> tag contains:
        #    2.1. a <div> tag: contains the subtotal and tax labels & values
        #    2.2. a <hr> tag
        #    2.3. a <p> tag: looks like it contains the name of the card used to pay: in this case "apple card",
        #         not  sure what values would be used if it was something other than the apple card
        #    2.4. a <div> tag: does not contain a label, but does contain the total value (subtotal + tax)

        # process the subtotal and tax values (item 2.1):
        # this content consist of multiple pairs of tags: a label nested within a <p> tag, followed by a
        # value nested inside a <div> we get all the text values of the <p> and <div> tags as 2 separate lists,
        # zip them together and create a dictionary object to access the values
        div_tag = section.div.find_all("div", recursive=False)[1]

        fields_names_values = self.parse_sect_3_fields(div_tag)
        self.set_sect_3_attribs(fields_names_values)
        # process the card name (item 2.3)
        # we need to use find_all("p") because if we just use .p -- we get <p> tags from item 2.2.1 -- wierd right?
        self.receipt_email.card = div_tag.find_all("p", recursive=False)[0].text.strip()
        # process the total value (item 2.4)
        self.receipt_email.total = self.parse_decimal(div_tag.find_all("div", recursive=False)[1].text.strip())

    @staticmethod
    def parse_sect_1_fields(section):
        # get all the child <div> tags
        section_1_div_tags = section.find_all("div", recursive=False)

        # each <div> tag contains a pair of <p> tags: the first one with a label, the second with a value
        # we loop through the <div> tags, getting each pair of labels and values, then create a dictionary
        # object to access the values
        items_pairs = []
        for div_tag in section_1_div_tags:
            p_tags = [p.text.strip() for p in div_tag.find_all("p", recursive=False)]
            items_pairs.append((p_tags[0].lower()[:-1], p_tags[1]))
        fields_names_values = dict(items_pairs)
        return fields_names_values

    @staticmethod
    def parse_sect_3_fields(div_tag):
        field_names = [t.text.strip().lower() for t in div_tag.div.find_all("p", recursive=False)]
        field_values = [t.text.strip() for t in div_tag.div.find_all("div", recursive=False)]
        fields_names_values = dict(zip(field_names, field_values))
        return fields_names_values

    def set_sect_1_attribs(self, fields_names_values):
        # validate the list of parsed field names
        invalid_fields = set(fields_names_values.keys()) - set(self.FIELD_ATTR_SECTION_1.keys())
        if invalid_fields:
            raise ValueError(
                f"section 1 - one or more undefined attributes: {invalid_fields} found in: {fields_names_values}")

        # assign each field name's value to its corresponding attribute
        for field_name, attr_name in self.FIELD_ATTR_SECTION_1.items():
            setattr(self.receipt_email, attr_name, fields_names_values.get(field_name, ""))

    def set_sect_3_attribs(self, fields_names_values):
        invalid_fields = set(fields_names_values.keys()) - set(self.FIELD_ATTR_SECTION_3.keys())
        if invalid_fields:
            raise ValueError(
                f"section 3 - one or more undefined attributes: {invalid_fields} found in: {fields_names_values}")
        for field_name, attr_name in self.FIELD_ATTR_SECTION_3.items():
            field_value = self.parse_decimal(fields_names_values.get(field_name, "$0.00"))
            setattr(self.receipt_email, field_name, field_value)

    @staticmethod
    def parse_date(date_str: str) -> date | None:
        """Parses a date string into a date object.

        If an invalid date sting is passed a value of None is returned.
        """
        try:
            return dap.parse(date_str.strip()).date()
        except dap.ParserError:
            # receipt_date is defaulted to None in __init__(), so no need to do anything if the date parse fails
            return None

    @staticmethod
    def parse_decimal(value_str: str) -> Decimal:
        """Parses a string value into a Decimal object.

        If an empty string is passed a value of Decimal("0.00") is returned.
        """
        value_str = value_str[1:] if value_str.startswith("$") else value_str
        return Decimal(value_str or "0.00")
