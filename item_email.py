from decimal import Decimal


class ItemEmail:
    """An email receipt item Data Transfer Object (DTO).

    This class encapsulates details relevant to an email receipt item, such as item
    category, descriptions, purchase amount, other related amounts, and an
    image link associated with the item. It is designed to provide structured
    storage and representation of the aforementioned item properties.

    :ivar item_category: Category of the item associated with the email.
    :type item_category: str | None
    :ivar descriptions: A list of textual descriptions of the item.
                        Each string represents an attribute or noteworthy
                        detail of the item.
    :type descriptions: list[str]
    :ivar purchase_amount: The monetary purchase amount of the item.
    :type purchase_amount: Decimal
    :ivar other_amount: An additional monetary amount related to the item,
                        defaulting to Decimal("0.00") if not provided.
    :type other_amount: Decimal | None
    :ivar image_link: A URL link pointing to an image resource of the item.
    :type image_link: str
    """
    ZERO_DECIMAL = Decimal("0.00")

    def __init__(
            self, item_category: str | None,
            descriptions: list[str],
            purchase_amount: Decimal,
            other_amount: Decimal | None,
            image_link:str
    ):
        self.item_category = item_category
        self.descriptions = descriptions
        self.purchase_amount = purchase_amount
        self.other_amount = other_amount or self.ZERO_DECIMAL
        self.image_link = image_link
