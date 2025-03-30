from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Self

import dateutil.parser as dap
from item_email import ItemEmail

# Constants
ZERO_DECIMAL = Decimal("0.00")


class ItemCategory(Enum):
    """Represents a category enumeration for items.

    This enumeration is used to categorize the different types of purchases.

    :cvar NONE: Represents no category.
    :cvar APP: Represents purchases from app-store category.
    :cvar TV: Represents purchases for the tv & movie category.
    :cvar SERVICE: Represents purchases for the service category.
    """
    NONE = 'none'
    APP = 'app'
    TV = 'tv'
    SERVICE = 'service'


class ItemType(Enum):
    """Represents an item types as an enumeration for purchased items.

    This enumeration provides various predefined types of items for use in applications and
    systems. It helps to manage and differentiate between different kinds of content or
    services, such as movies, subscriptions, or in-app purchases.

    :ivar MOVIE_RENTAL: Represents an item categorized as a movie rental.
    :type MOVIE_RENTAL: str
    :ivar MOVIE_PURCHASE: Represents an item categorized as a movie purchase.
    :type MOVIE_PURCHASE: str
    :ivar IN_APP_PURCHASE: Represents an item categorized as an in-app purchase.
    :type IN_APP_PURCHASE: str
    :ivar STREAMING_SUBSCRIPTION: Represents an item categorized as a streaming subscription.
    :type STREAMING_SUBSCRIPTION: str
    :ivar SOFTWARE_SUBSCRIPTION: Represents an item categorized as a software subscription.
    :type SOFTWARE_SUBSCRIPTION: str
    :ivar SERVICE_SUBSCRIPTION: Represents an item categorized as a service subscription.
    :type SERVICE_SUBSCRIPTION: str
    :ivar INDIVIDUAL_SUBSCRIPTION: Represents an item categorized as an individual subscription.
    :type INDIVIDUAL_SUBSCRIPTION: str
    :ivar IN_APP_MOVIE_RENTAL: Represents an item categorized as an in-app movie rental.
    :type IN_APP_MOVIE_RENTAL: str
    :ivar UNKNOWN: Represents an unknown or unclassified item.
    :type UNKNOWN: None
    """
    MOVIE_RENTAL = 'movie rental'
    MOVIE_PURCHASE = 'movie purchase'
    IN_APP_PURCHASE = 'in app purchase'
    STREAMING_SUBSCRIPTION = 'streaming subscription'
    SOFTWARE_SUBSCRIPTION = 'software subscription'
    SERVICE_SUBSCRIPTION = 'service subscription'
    INDIVIDUAL_SUBSCRIPTION = 'individual subscription'
    IN_APP_MOVIE_RENTAL = 'in app movie rental'
    UNKNOWN = 'unknown'


class SubscriptionFrequency(Enum):
    """Represents the frequency of a subscription.

    This enumeration is used to define the different possible frequencies that
    a subscription can have. It is useful in scenarios where the recurring
    interval of a subscription needs to be specified or determined. The options
    include monthly, yearly, or an unknown frequency which acts as a default
    placeholder when the frequency is not defined.

    :cvar MONTHLY: Indicates that the subscription is billed on a monthly basis.
    :cvar ANNUAL: Indicates that the subscription is billed on a yearly basis.
    :cvar UNKNOWN: Represents an undefined or unknown subscription frequency.
    """
    MONTHLY = 'monthly'
    SEMI_ANNUAL = 'semi-annual'
    ANNUAL = 'annual'
    UNKNOWN = None


# which item types are taxable
TAXABLE_ITEM_TYPES = [
    ItemType.IN_APP_PURCHASE,
    ItemType.SOFTWARE_SUBSCRIPTION,
    ItemType.SERVICE_SUBSCRIPTION,  # note not all services are taxable
]

# this is the list of recognized streaming subscriptions
STREAMING_SUBSCRIPTIONS = [
    "max standard",
    "max ad-free",
    "hbo max ad-free",
    "starz",
]

# this is the list of recognized software subscriptions
SOFTWARE_SUBSCRIPTIONS = [
    "copilot: track & budget money",
    "bumble - dating. friends. bizz",
    "coffee meets bagel dating app",
    "hinge dating app: meet people",
    "noom: healthy weight loss",
    "paramount+",
    "snapchat",


]

# this is the list of recognized service subscriptions
SERVICE_SUBSCRIPTIONS = [
    "family",
    "premier",
    "apple news+"
]

# this is the list of recognized apple one subscription levels
APPLE_ONE_SUBSCRIPTION_LEVELS = [
    "individual",
    "family",
    "premier",
]

# this is the list of individual app-store game subscriptions
INDIVIDUAL_SUBSCRIPTIONS = [
    "nyt games: word, number, logic",
    "bumble - dating. friends. bizz",
    "coffee meets bagel dating app",
    "hinge dating app: meet people",
    "paramount+",
    "snapchat",
]


class Item:
    """Represents a specific receipt item with detailed metadata.

    This class encapsulates the properties and mechanisms to define an individual
    item's details, including its category, descriptions, monetary amounts, image
    URL, and derived attributes like taxable status, item type, and other metadata.
    It also contains methods for creating objects from DTOs and processing
    descriptions to populate characteristics such as the item's type and
    subscription-related details.

    :ivar item_category: The category assigned to this item.
    :type item_category: ItemCategory
    :ivar purchase_amount: The purchase price of the item.
    :type purchase_amount: Decimal
    :ivar other_amount: Any additional associated monetary amount.
    :type other_amount: Decimal
    :ivar image_url: A string representing the URL of an associated image.
    :type image_url: str
    :ivar tax_applied: The tax applied to the item, initialized to zero.
    :type tax_applied: Decimal
    :ivar total_amount: The total cost including tax, initialized to zero.
    :type total_amount: Decimal
    :ivar item_type: The type of item derived from its descriptions.
    :type item_type: ItemType
    :ivar description_1: The primary description text associated with the item.
    :type description_1: str
    :ivar description_2: The secondary description text associated with the item, if applicable.
    :type description_2: str | None
    :ivar subscription_frequency: The frequency of the subscription, if the item is a subscription.
    :type subscription_frequency: SubscriptionFrequency | None
    :ivar next_renewal_date: The renewal date, determined from descriptions, for subscriptions.
    :type next_renewal_date: str | None
    :ivar device: user device that the item was purchased from, if applicable.
    :type device: str | None
    :ivar taxable: Whether the item is taxable, derived from its type.
    :type taxable: bool
    """
    def __init__(self,
                 item_category: ItemCategory,
                 description_list: list[str],
                 purchase_amount: Decimal,
                 other_amount: Decimal,
                 image_url: str):
        """Creates a new Receipt Item object deriving details from the specified item description list.

        This class is used to create an item object with specified details for its category,
        descriptions, monetary attributes, and a potential image URL. It processes description
        text to determine specific attributes (e.g., item type, subscription frequency, etc.).
        It also checks the taxable status of the item based on its type and contains placeholders
        for tax information and total amounts.

        :param item_category: The category to which the item belongs.
        :type item_category: ItemCategory
        :param description_list: List of textual descriptions related to the item.
        :type description_list: list[str]
        :param purchase_amount: Monetary amount representing the item's purchase price.
        :type purchase_amount: Decimal
        :param other_amount: Additional monetary amount possibly associated with the item.
        :type other_amount: Decimal
        :param image_url: A URL string to an image associated with the item.
        :type image_url: str
        """
        self.item_category = item_category
        self.purchase_amount = purchase_amount
        self.other_amount = other_amount
        self.image_url = image_url

        self.tax_applied = ZERO_DECIMAL  # default the item's tax to 0
        self.total_amount = ZERO_DECIMAL  # set the item total to 0, so that its obvious if tax was not applied

        # Normalizes all descriptions to lowercase
        description_list = [desc.lower() for desc in description_list]

        # determine the attribute values by using the list of descriptions for the item that were
        # extracted from the receipt email
        self.item_type = self.determine_item_type(description_list)
        self.description_1 = self.determine_description_1(description_list)
        self.description_2 = self.determine_description_2(description_list)
        self.subscription_frequency = self.determine_subscription_frequency(description_list)
        self.next_renewal_date = self.determine_renewal_date(description_list)
        self.device = self.determine_device(description_list)

        # set taxable to True if item type is in the list of taxable item types
        self.taxable = self.item_type in TAXABLE_ITEM_TYPES

    @classmethod
    def from_item_email(cls, item_email_dto: ItemEmail) -> Self:
        """Creates an instance of the Item class using data from an ItemEmail DTO.

        This method is responsible for converting an instance of the ItemEmail
        DTO into an instance of the Item class. The provided DTO contains data
        fields that are utilized to initialize the class attributes.

        :param item_email_dto: Data Transfer Object containing information about
            the item, including category, descriptions, purchase amount,
            additional amount, and image URL.
        :type item_email_dto: ItemEmail

        :return: An instance of the Item class created from the input DTO.
        :rtype: Self
        """
        return cls(
            item_category=ItemCategory(item_email_dto.item_category or "none"),
            description_list=item_email_dto.descriptions,
            purchase_amount=item_email_dto.purchase_amount,
            other_amount=item_email_dto.other_amount,
            image_url=item_email_dto.image_link,
        )

    @staticmethod
    def stream_desc(desc) -> str:
        """Clean the streaming subscription description string.

        Static method to process and clean up the streaming subscription description string by removing specific
        unnecessary substrings such as "monthly", " (monthly)", and " (automatic renewal)". This is useful
        for standardizing the representation of subscription descriptions by stripping redundant text.

        :param desc: The original streaming subscription description string to process.
        :type desc: str
        :return: A cleaned streaming subscription description string with specified substrings removed.
        :rtype: str
        """
        return desc.replace(" monthly", "").replace(" (monthly)", "").replace(" (automatic renewal)", "")

    @staticmethod
    def srvc_desc(desc) -> str:
        """Clean the service subscription description string.

        Static method to process and clean up the service subscription description string by removing specific
        unnecessary substrings such as "monthly", and " (automatic renewal)". This is useful
        for standardizing the representation of subscription descriptions by stripping redundant text.

        :param desc: The original service subscription description string to process.
        :type desc: str
        :return: The cleaned service subscription description string with specified substrings removed.
        :rtype: str
        """
        return desc.replace(" monthly", "").replace(" (automatic renewal)", "").replace("\u00A0", " ")

    def determine_item_type(self, desc_lst) -> ItemType:
        """Determines the type of item based on its description.

        This function evaluates the provided description list and determines the
        appropriate `ItemType` for the item. The decision is made based on various
        criteria such as the number of elements in the description list and the
        content of specific positions that correspond to certain item types
        (e.g., movie rental, streaming subscription, etc.). If no matching
        criteria are found, the function defaults to returning `ItemType.UNKNOWN`.

        :param desc_lst: A list containing the item's description. Each element in
            the list provides details such as category or specific properties
            required to determine the item's type.
        :type desc_lst: list
        :return: The type of the item as determined based on the description provided.
        :rtype: ItemType
        """
        desc_len = len(desc_lst)
        if desc_len == 4 and desc_lst[2] == "movie rental":
            return ItemType.MOVIE_RENTAL
        elif desc_len == 4 and desc_lst[2] == "movie":
            return ItemType.MOVIE_PURCHASE
        elif desc_len == 4 and desc_lst[2] == "in-app purchase":
            return ItemType.IN_APP_PURCHASE
        elif desc_len == 3 and desc_lst[1] == "in-app purchase":
            return ItemType.IN_APP_MOVIE_RENTAL
        elif desc_len == 3 and desc_lst[2].startswith("renews") and self.stream_desc(desc_lst[1]) in STREAMING_SUBSCRIPTIONS:
            return ItemType.STREAMING_SUBSCRIPTION
        elif desc_len == 3 and desc_lst[2].startswith("renews") and desc_lst[0] in SOFTWARE_SUBSCRIPTIONS:
            return ItemType.SOFTWARE_SUBSCRIPTION
        elif desc_len == 3 and desc_lst[2].startswith("renews") and self.srvc_desc(desc_lst[0]) in SERVICE_SUBSCRIPTIONS:
            return ItemType.SERVICE_SUBSCRIPTION
        elif desc_len == 4 and desc_lst[2].startswith("renews") and desc_lst[0] in INDIVIDUAL_SUBSCRIPTIONS:
            return ItemType.INDIVIDUAL_SUBSCRIPTION
        else:
            return ItemType.UNKNOWN

    def determine_description_1(self, desc_lst) -> str:
        """Determines the first description string.

        Determines and returns the primary description based on the item type and the
        contents of the provided description list. The behavior and logic for
        constructing the description depend on the specific item type the object
        contains.

        :param desc_lst: A list of description strings relevant to the item's type.
        :type desc_lst: list
        :return: A description string determined based on the item's type and
                 the provided description list.
        :rtype: str
        :raises ValueError: If the item's type is unexpected or invalid.
        """
        if self.item_type == ItemType.STREAMING_SUBSCRIPTION:
            stream_desc = self.stream_desc(desc_lst[0])
            if ":" in stream_desc:
                return stream_desc.split(":")[0].strip()
            elif "apple tv" in stream_desc:
                return self.stream_desc(desc_lst[1])
            else:
                return stream_desc
        elif self.item_type in [ItemType.SOFTWARE_SUBSCRIPTION, ItemType.INDIVIDUAL_SUBSCRIPTION]:
            if ":" in desc_lst[0]:
                return desc_lst[0].split(":")[0].strip()
            else:
                return desc_lst[0]
        elif self.item_type == ItemType.SERVICE_SUBSCRIPTION:
            srvc_desc = self.srvc_desc(desc_lst[0])
            if srvc_desc in APPLE_ONE_SUBSCRIPTION_LEVELS:
                return "apple one"
            else:
                return srvc_desc
        elif self.item_type in [
            ItemType.MOVIE_RENTAL, ItemType.MOVIE_PURCHASE, ItemType.IN_APP_PURCHASE,
            ItemType.IN_APP_MOVIE_RENTAL, ItemType.UNKNOWN
        ]:
            return desc_lst[0]
        else:
            raise ValueError(f"Unexpected item type: {self.item_type} in determine_description_1")

    def determine_description_2(self, desc_lst) -> str | None:
        """Determines the second description string.

        Determines and returns the secondary description based on the item type and the
        contents of the provided description list. The behavior and logic for
        constructing the description depend on the specific item type the object
        contains.

        :param desc_lst: A list of description strings relevant to the item's type.
        :type desc_lst: list
        :return: A description string determined based on the item's type and
                 the provided description list.
        :rtype: str
        :raises ValueError: If the item's type is unexpected or invalid.
        """
        if self.item_type in [ItemType.MOVIE_RENTAL, ItemType.MOVIE_PURCHASE, ItemType.IN_APP_PURCHASE]:
            return desc_lst[1]
        elif self.item_type == ItemType.STREAMING_SUBSCRIPTION:
            stream_desc = self.stream_desc(desc_lst[0])
            if ":" in stream_desc:
                return stream_desc.split(":", 1)[1].strip()
            else:
                return None
        elif self.item_type in [ItemType.SOFTWARE_SUBSCRIPTION, ItemType.INDIVIDUAL_SUBSCRIPTION]:
            if ":" in desc_lst[0]:
                return desc_lst[0].split(":", 1)[1].strip()
            else:
                return None
        elif self.item_type == ItemType.SERVICE_SUBSCRIPTION:
            srvc_desc = self.srvc_desc(desc_lst[0])
            if srvc_desc in APPLE_ONE_SUBSCRIPTION_LEVELS:
                return srvc_desc
            else:
                return None
        elif self.item_type == ItemType.UNKNOWN:
            return "|".join(desc_lst[1:])
        elif self.item_type == ItemType.IN_APP_MOVIE_RENTAL:
            return None
        else:
            raise ValueError(f"Unexpected item type: {self.item_type} in determine_description_2")

    def determine_subscription_frequency(self, desc_lst) -> SubscriptionFrequency | None:
        """Determines the subscription frequency.

        Determine the frequency of a subscription based on the item type and description list.

        This function inspects the `item_type` attribute of the class to categorize the
        frequency of a subscription. It considers types such as streaming subscriptions,
        software subscriptions, service subscriptions, and individual subscriptions. The function
        examines key phrases within the second element of `desc_lst` to determine whether the
        subscription is monthly, yearly, or unknown. Non-subscription related item types will
        result in a return value of `None`. For any unhandled `item_type`, an exception is raised.

        The function leverages specific item-type categories and corresponding descriptions
        to ensure accurate subscription frequency determination while handling exceptional or
        non-relevant item types gracefully.

        :param desc_lst: The description list associated with the item, where the frequency
            keyword is typically located in the second index.
        :type desc_lst: list
        :return: The subscription frequency categorized as an attribute of the `SubscriptionFrequency`
            enumeration, or `None` if the item type does not include subscription relevance.
        :rtype: SubscriptionFrequency | None

        :raises ValueError: If the `item_type` contains an unexpected or unhandled value.
        """
        if self.item_type in [
            ItemType.STREAMING_SUBSCRIPTION, ItemType.SOFTWARE_SUBSCRIPTION, ItemType.SERVICE_SUBSCRIPTION,
            ItemType.INDIVIDUAL_SUBSCRIPTION
        ]:
            if any(val in desc_lst[1] for val in ["(monthly)", "monthly", ]):
                return SubscriptionFrequency.MONTHLY
            elif any(val in desc_lst[1] for val in ["6 month"]):
                return SubscriptionFrequency.SEMI_ANNUAL
            elif any(val in desc_lst[1] for val in ["(annual)", "(yearly)", ]):
                return SubscriptionFrequency.ANNUAL
            else:
                return SubscriptionFrequency.UNKNOWN
        elif self.item_type in [
            ItemType.MOVIE_RENTAL, ItemType.MOVIE_PURCHASE, ItemType.IN_APP_PURCHASE,
            ItemType.IN_APP_MOVIE_RENTAL, ItemType.UNKNOWN
        ]:
            return None
        else:
            raise ValueError(f"Unexpected item type: {self.item_type} in determine_subscription_frequency")

    def determine_renewal_date(self, desc_lst) -> date | None:
        """Determines the subscription renewal date.

        Determines the renewal date of an item based on its type and the provided description list.

        This method processes the description list (`desc_lst`) to parse and determine a renewal date
        depending on the `item_type` associated with the object. Certain item types that represent
        subscriptions are processed to extract their renewal dates, while other item types are set
        to return `None`. If the item type is unexpected, a `ValueError` is raised to signal improper input.

        :param desc_lst: A list of strings that contain details related to the item, including
            subscription data that can be parsed for the renewal date.
        :type desc_lst: list[str]
        :return: The date if extracted successfully for certain types, or None for unsupported types.
        :rtype: date | None
        :raises ValueError: If the item type is unexpected or outside the range of recognized categories.
        """
        if self.item_type in [
            ItemType.STREAMING_SUBSCRIPTION, ItemType.SOFTWARE_SUBSCRIPTION, ItemType.SERVICE_SUBSCRIPTION,
            ItemType.INDIVIDUAL_SUBSCRIPTION
        ]:
            try:
                return dap.parse(desc_lst[2][7:]).date()
            except dap.ParserError:
                return None
        elif self.item_type in [
                ItemType.MOVIE_RENTAL, ItemType.MOVIE_PURCHASE, ItemType.IN_APP_PURCHASE,
                ItemType.IN_APP_MOVIE_RENTAL, ItemType.UNKNOWN
        ]:
            return None
        else:
            raise ValueError(f"Unexpected item type: {self.item_type} in determine_renewal_date")

    def determine_device(self, desc_lst) -> str | None:
        """Determines the user device that was used to make the purchase.

        Determines the user device based on the provided description list and the
        item type. Different item types require extracting the device information
        from different indices of the description list. For unsupported or unknown
        item types, it either returns None or raises a `ValueError`.

        :param desc_lst: A list of descriptions used to determine the device type.
        :return: The determined device type as a string, or None if the device type
            cannot be determined.
        :rtype: str | None
        :raises ValueError: If the `item_type` is unexpected or not defined for this
            functionality.
        """
        if self.item_type in [
            ItemType.MOVIE_RENTAL, ItemType.MOVIE_PURCHASE, ItemType.IN_APP_PURCHASE,
            ItemType.INDIVIDUAL_SUBSCRIPTION
        ]:
            return desc_lst[3]
        elif self.item_type == ItemType.IN_APP_MOVIE_RENTAL:
            return desc_lst[2]
        elif self.item_type in [
            ItemType.STREAMING_SUBSCRIPTION, ItemType.SOFTWARE_SUBSCRIPTION, ItemType.SERVICE_SUBSCRIPTION,
            ItemType.UNKNOWN
        ]:
            return None
        else:
            raise ValueError(f"Unexpected item type: {self.item_type} in determine_device")

    def apply_tax(self, tax_rate: Decimal) -> Decimal:
        """Apply tax to the item's purchase amount.

        Calculates and applies a tax to a purchase amount if the item is taxable.
        Modifies internal state by updating the tax applied and the total amount
        based on the tax rate provided. It ensures precision by quantizing the tax
        value to two decimal places.

        :param tax_rate: The rate of tax to be applied to the purchase amount.
        :type tax_rate: Decimal
        :return: The calculated tax amount, rounded to two decimal places.
        :rtype: Decimal
        """
        self.tax_applied = Decimal("0.00")
        if self.taxable:
            self.tax_applied = self.calc_tax(tax_rate)
        self.total_amount = self.purchase_amount + self.tax_applied
        return self.tax_applied

    def calc_tax(self, tax_rate):
        return (self.purchase_amount * tax_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def adjust_tax(self, tax_adjustment: Decimal) -> None:
        """Adjust the tax amount and total amount of the item by the tax adjustment.

        Adjusts the `tax_applied` and the `total_amount` of the item by adding the
        specified positive or negative tax adjustment value.

        :param tax_adjustment: The adjustment value to add to the current tax applied.
        :type tax_adjustment: Decimal
        """
        self.tax_applied += tax_adjustment
        self.total_amount += tax_adjustment

    def insert(self, curs, hdr_id):
        sql = """
            insert into item_detail (
                hdr_id, 
                item_category, 
                item_type, 
                description_1, 
                description_2, 
                purchase_amount, 
                other_amount, 
                tax_applied, 
                total_amount, 
                subscription_frequency, 
                next_renewal_date, 
                device, 
                image_url
            ) values (
                :hdr_id,
                :item_category,
                :item_type,
                :description_1,
                :description_2,
                :purchase_amount,
                :other_amount,
                :tax_applied,
                :total_amount,
                :subscription_frequency,
                :next_renewal_date,
                :device,
                :image_url
            )
        """
        curs.execute(sql, {
            "hdr_id": hdr_id,
            "item_category": self.item_category.value,
            "item_type": self.item_type.value,
            "description_1": self.description_1,
            "description_2": self.description_2,
            "purchase_amount": float(self.purchase_amount),
            "other_amount": float(self.other_amount) if self.other_amount else None,
            "tax_applied": float(self.tax_applied),
            "total_amount": float(self.total_amount),
            "subscription_frequency": self.subscription_frequency.value if self.subscription_frequency else None,
            "next_renewal_date": self.next_renewal_date,
            "device": self.device,
            "image_url": self.image_url,
        })

