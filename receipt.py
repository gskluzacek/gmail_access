from datetime import date
from decimal import Decimal
from typing import Self

from bs4 import BeautifulSoup, formatter

from item import Item
from receipt_email import ReceiptEmail


class Receipt:
    """Representation of a purchase receipt along with the items purchased in the transaction.

    This class models the details of a receipt from a transaction and provides functionality
    to itemize purchased goods, apply tax, and manage payment records. Each instance contains
    comprehensive details about the purchase, including the date, order ID, associated payment
    account, monetary breakdowns (subtotal, tax, and total), and any applicable items that are
    part of the receipt.

    :ivar tax_rate: The standard tax rate applied to items in the receipt.
    :type tax_rate: decimal.Decimal
    :ivar receipt_date: The date of the transaction associated with the receipt.
    :type receipt_date: datetime.date
    :ivar order_id: A unique identifier for the transaction or order.
    :type order_id: str
    :ivar doc_nbr: The document or receipt number for the transaction.
    :type doc_nbr: str
    :ivar apple_account: The Apple account used to conduct the transaction.
    :type apple_account: str
    :ivar subtotal: The subtotal amount, which excludes tax.
    :type subtotal: decimal.Decimal
    :ivar tax: The total tax amount calculated or charged for the transaction.
    :type tax: decimal.Decimal
    :ivar total: The final amount charged, inclusive of both subtotal and tax.
    :type total: decimal.Decimal
    :ivar card: The payment card used for the transaction, if any.
    :type card: str | None
    :ivar file_path: The file path used to store the receipt information, if applicable.
    :type file_path: str | None
    :ivar items: A list of purchased items associated with the receipt.
    :type items: list[Item]
    """
    tax_rate: Decimal = Decimal("0.08")

    def __init__(self,
        soup: BeautifulSoup,
        receipt_date: date,
        order_id: str,
        doc_nbr: str,
        apple_account: str,
        subtotal: Decimal,
        tax: Decimal,
        card: str | None,
        total: Decimal,
        items: list[Item] | None = None,
    ):
        """Create a new Receipt object.

        Represents a purchase receipt containing information about the order details,
        payment, and associated purchased items. It provides data fields for details
        such as receipt date, order ID, document number, account, subtotal, tax,
        payment card, total amount, and file path. It includes itemized purchase
        details and offers functionality to save receipt details to a file.

        :param receipt_date: The date associated with the purchase receipt.
        :type receipt_date: datetime.date
        :param order_id: Unique identifier for the order.
        :type order_id: str
        :param doc_nbr: Document or receipt number for the transaction.
        :type doc_nbr: str
        :param apple_account: Apple account used that made the purchase.
        :type apple_account: str
        :param subtotal: The subtotal amount before tax.
        :type subtotal: decimal.Decimal
        :param tax: The tax amount charged for the purchase.
        :type tax: decimal.Decimal
        :param card: The payment card information used for the transaction.
        :type card: str | None
        :param total: The total amount after tax (if applicable).
        :type total: decimal.Decimal
        :param file_path: The file path to save the receipt details.
        :type file_path: str | None
        :param items: List of `Item` objects representing the purchased items.
            if None is passed, then the list of items is initialized to an empty list.
        :type items: list[Item] | None
        """
        self.soup = soup
        self.receipt_date = receipt_date
        self.order_id = order_id
        self.doc_nbr = doc_nbr
        self.apple_account = apple_account
        self.subtotal = subtotal
        self.tax = tax
        self.total = total
        self.card = card.replace("\u00A0", " ") if card else None
        self.file_path = None
        self.items: list[Item] = items or []
        if self.items:
            self.apply_tax_to_items()

    @classmethod
    def from_receipt_email(cls, receipt_email_dto: ReceiptEmail) -> Self:
        """Creates an instance of the Receipt class using data from an ItemEmail DTO.

        This method is responsible for converting an instance of the ReceiptEmail DTO into an
        instance of the Receipt class along with its corresponding Item objects and applies any
        necessary tax computations to the items in the receipt. The provided DTO contains data
        fields that are utilized to initialize the class attributes.

        :param receipt_email_dto: Data Transfer Object containing information about the receipt
            including, order details, monetary values, and associated items.
        :type receipt_email_dto: ReceiptEmail
        :return: An instance of the Receipt class & list of Item class instances created from
            the input DTO.
        :rtype: Self
        """
        receipt = Receipt(
            soup=receipt_email_dto.soup,
            receipt_date=receipt_email_dto.receipt_date,
            order_id=receipt_email_dto.order_id,
            doc_nbr=receipt_email_dto.doc_nbr,
            apple_account=receipt_email_dto.apple_account,
            subtotal=receipt_email_dto.subtotal,
            tax=receipt_email_dto.tax,
            card=receipt_email_dto.card,
            total=receipt_email_dto.total,
        )
        for item_email_dto in receipt_email_dto.items:
            receipt.add_item(Item.from_item_email(item_email_dto))
        receipt.apply_tax_to_items()
        return receipt

    def add_item(self, item: Item) -> None:
        """Adds an item to the list of the receipt's items.

        :param item: the item to be added to the receipt
        :type item: Item
        """
        self.items.append(item)

    def apply_tax_to_items(self) -> None:
        """Apply tax to each taxable item on the receipt.

        Apply tax to each item purchased and ensure the sum of taxes matches the total tax specified for the receipt.
        An adjustment is applied to a specific item if there is a rounding discrepancy between the calculated total tax
        from individual items and the receipt's total tax.

        :raises ValueError: When the calculated total tax for all items is less than or equal to zero, and it is
            not possible to determine the item for tax adjustment.
        """
        # apply tax to each item purchased and then sum up the tax calculated for all individual items
        items_tax_calc = [item.apply_tax(self.tax_rate) for item in self.items]
        total_tax_calc = sum(items_tax_calc)

        # if self.tax is non-zero but none of the items were marked as taxable, then check if a single item accounts for the entire tax amount
        if self.tax != Decimal("0.00") and total_tax_calc == Decimal("0.00"):
            items_tax_calc_ovrd = [item.calc_tax(self.tax_rate) for item in self.items]
            appy_tax_to_accountable_item_index = next((i for i, tax_amt in enumerate(items_tax_calc_ovrd) if tax_amt == self.tax), None)
            if appy_tax_to_accountable_item_index is None:
                raise ValueError(f"The receipt has tax amount of: {self.tax}, however none of the items are marked as taxable. Additionally, no one item accounts for the entire tax amount")
            item = self.items[appy_tax_to_accountable_item_index]
            print(f"applying tax amount of: ${self.tax} to item: {item.description_1} for receipt: {self.order_id}")
            self.items[appy_tax_to_accountable_item_index].adjust_tax(self.tax)

        else:
            tax_adj = self.tax - total_tax_calc
            if tax_adj:
                # get the index of the first item with a non-zero tax amount, if all items have a zero tax amount,
                # None is returned

                # implementation notes:
                #   1) we use a generator function to yield each value on demand
                #   2) the value of i is only yielded if item_tax_amt is non-zero
                #   3) next() stops as soon as it retrieves the first value from the generator expression
                #   4) if no values satisfy the condition of the generator function, next() will return the default value
                #      of None
                apply_adj_to_index = next((i for i, item_tax_amt in enumerate(items_tax_calc) if item_tax_amt), None)

                if apply_adj_to_index is None:
                    raise ValueError(
                        f"Error in apply tax to items. After applying tax to each taxable item, a tax adjustment of "
                        f"${tax_adj} was required due to rounding. Tax on receipt: ${self.tax}, total tax calculated: "
                        f"${total_tax_calc}. However the tax calculated for all items was less than +0.00! So we could "
                        f"not determine which item to apply the tax adjustment to. Individual tax amounts calculated: "
                        f"{", ".join([str(tax) for tax in items_tax_calc])}."
                    )

                # if the tax adjustment exceeds the threshold of $0.04, validate that the number of items on the
                # receipt is one, else raise an exception
                if abs(tax_adj) > Decimal("0.04"):
                    number_of_taxable_items = sum(1 for item_tax_amt in items_tax_calc if item_tax_amt)
                    if number_of_taxable_items > 1:
                        raise ValueError(
                            f"A significant tax adjustment of ${tax_adj} is required which usually indicates that only part"
                            f"of the purchase amount of an item is taxable or that the item type is only sometimes taxable."
                            f"Additionally, the number of taxable items on the receipt: {number_of_taxable_items}, is "
                            f"greater than one. As such, it cannot be determined which item to apply the tax adjustment to."
                        )
                    item = self.items[apply_adj_to_index]
                    print(f"Applied a significant tax adjustment of: ${tax_adj} to item: > {item.description_1} < for receipt: {self.order_id}")
                self.items[apply_adj_to_index].adjust_tax(tax_adj)
        # set subtotal if it is 0.00
        self.subtotal = self.subtotal or self.total - self.tax

    def save(self, dir_path: str) -> None:
        receipt_file_path = f"{dir_path}/{self.order_id}_{self.receipt_date.strftime("%Y-%m-%d")}.html"
        pretty_html = self.soup.prettify(formatter=formatter.HTMLFormatter(indent=4))
        with open(receipt_file_path, 'w') as f:
            f.write(pretty_html)
        self.file_path = receipt_file_path

    def exists(self, conn):
        curs = conn.cursor()
        sql = """
            select hdr_id from order_header where order_id = :order_id;
        """
        curs.execute(sql, {"order_id": self.order_id})
        row = curs.fetchone()
        if row:
            hdr_id = row.hdr_id
        else:
            hdr_id = None
        curs.close()
        return hdr_id

    def insert(self, conn):
        curs = conn.cursor()
        sql = """
            insert into order_header (
                receipt_date, 
                order_id, 
                doc_nbr, 
                apple_account, 
                subtotal, 
                tax, 
                total, 
                card, 
                file_path
            ) values (
                :receipt_date,
                :order_id,
                :doc_nbr,
                :apple_account,
                :subtotal, 
                :tax,
                :total,
                :card,
                :file_path
            )
        """
        curs.execute(sql, {
            "receipt_date": self.receipt_date,
            "order_id": self.order_id,
            "doc_nbr": self.doc_nbr,
            "apple_account": self.apple_account,
            "subtotal": float(self.subtotal),
            "tax": float(self.tax),
            "total": float(self.total),
            "card": self.card,
            "file_path": self.file_path,
        })
        hdr_id = curs.lastrowid
        for item in self.items:
            item.insert(curs, hdr_id)
        conn.commit()
