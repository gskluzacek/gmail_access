import decimal
import pytest
from datetime import date, datetime
from decimal import Decimal
from item import Item, ItemCategory, ItemType, SubscriptionFrequency


class TestStreamDesc:
    @pytest.mark.parametrize(
        "input_desc, expected_output",
        [
            ("Premium Plan monthly", "Premium Plan"),
            ("Standard Plan (monthly)", "Standard Plan"),
            ("Basic Plan (automatic renewal)", "Basic Plan"),
            ("Pro Plan", "Pro Plan"),
        ]
    )
    def test_stream_desc_removes_unwanted_phrases(self, input_desc, expected_output):
        assert Item.stream_desc(input_desc) == expected_output

    @pytest.mark.parametrize(
        "input_desc, expected_output",
        [
            ("Service monthly", "Service"),
            ("Subscription (automatic renewal)", "Subscription"),
            ("Custom Text monthly (automatic renewal)", "Custom Text"),
            ("One-time Purchase", "One-time Purchase"),
        ]
    )
    def test_srvc_desc_removes_unwanted_phrases(self, input_desc, expected_output):
        assert Item.srvc_desc(input_desc) == expected_output


@pytest.mark.parametrize(
    "desc_lst, item_type, expected_device",
    [
        (['Blink Twice', 'Thriller', 'Movie Rental', "Device A"], ItemType.MOVIE_RENTAL, "Device A"),
        (['Heretic', 'Thriller', 'Movie', "Device B"], ItemType.MOVIE_PURCHASE, "Device B"),
        (['Gardenscapes', 'Botanist Kit', 'In-App Purchase', "Device C"], ItemType.IN_APP_PURCHASE, "Device C"),
        (['Max: Stream HBO, TV, & Movies', 'Max Standard Monthly (Monthly)', 'Renews March 24, 2025'], ItemType.STREAMING_SUBSCRIPTION, None),
        (['Copilot: Track & Budget Money', 'Yearly subscription (Annual)', 'Renews February 12, 2026'], ItemType.SOFTWARE_SUBSCRIPTION, None),
        (['Premier (Automatic Renewal)', 'Premier (Automatic Renewal) (Monthly)', 'Renews Dec 18, 2024'], ItemType.SERVICE_SUBSCRIPTION, None),
        (['NYT Games: Word, Number, Logic', 'Games - Annual (Yearly)', 'Renews Sep 24, 2025', "Device G"], ItemType.INDIVIDUAL_SUBSCRIPTION, "Device G"),
        (["Dr. Seuss' How the Grinch Stol", 'In-App Purchase', "Device H"], ItemType.IN_APP_MOVIE_RENTAL, "Device H"),
        (["unknown 1", "unknown 2", "unknown 3", "unknown 4"], ItemType.UNKNOWN, None),
    ],
)
def test_determine_device(desc_lst, item_type, expected_device):
    item = Item(
        item_category=ItemCategory.APP,
        description_list=desc_lst,
        purchase_amount=Decimal("10.00"),
        other_amount=Decimal("0.00"),
        image_url="Test URL",
    )
    item.item_type = item_type  # Set the item type manually
    assert item.determine_device(desc_lst) == expected_device


class TestItem:
    def test_determine_renewal_date_valid_subscription_type(self):
        # Test with valid subscription types and valid dates
        desc_lst = ["Service Plan", "Subscription", "Renews: Mar 15, 2024"]
        item = Item(
            item_category=ItemCategory.APP,
            description_list=desc_lst,
            purchase_amount=Decimal("5.00"),
            other_amount=Decimal("0.00"),
            image_url="Test URL",
        )
        item.item_type = ItemType.STREAMING_SUBSCRIPTION
        expected_date = datetime.strptime("Mar 15, 2024", "%b %d, %Y").date()
        assert item.determine_renewal_date(desc_lst) == expected_date

    def test_determine_renewal_date_non_subscription_type(self):
        # Test with non-subscription item type that should return None
        desc_lst = ["One-time Purchase", "HD", "Renews: Apr 20, 2024"]
        item = Item(
            item_category=ItemCategory.TV,
            description_list=desc_lst,
            purchase_amount=Decimal("10.00"),
            other_amount=Decimal("0.00"),
            image_url="Test URL",
        )
        item.item_type = ItemType.MOVIE_PURCHASE
        assert item.determine_renewal_date(desc_lst) is None

    def test_determine_renewal_date_missing_date_string(self):
        # Test with a valid subscription item type but no date string in the description list
        desc_lst = ["Service Plan", "Subscription", "No Renewal Info"]
        item = Item(
            item_category=ItemCategory.APP,
            description_list=desc_lst,
            purchase_amount=Decimal("5.00"),
            other_amount=Decimal("0.00"),
            image_url="Test URL",
        )
        item.item_type = ItemType.STREAMING_SUBSCRIPTION
        assert item.determine_renewal_date(desc_lst) is None

    @pytest.mark.parametrize(
        "desc_lst, expected_taxable",
        [
            (['Gardenscapes', 'Botanist Kit', 'In-App Purchase', "Device C"], True),
            (['Heretic', 'Thriller', 'Movie', "Device B"], False),
        ],
    )
    def test_taxable_attribute_based_on_item_type(self, desc_lst, expected_taxable):
        # Create an instance of Item
        item = Item(
            item_category=ItemCategory.APP,
            description_list=desc_lst,
            purchase_amount=Decimal("10.00"),
            other_amount=Decimal("0.00"),
            image_url="Test Image URL"
        )

        # Validate if the taxable attribute is set correctly based on the item_type
        assert item.taxable == expected_taxable

    @pytest.mark.parametrize(
        "desc_list, item_type, expected_frequency",
        [
            (["Subscription Plan", "(monthly)"], ItemType.STREAMING_SUBSCRIPTION, SubscriptionFrequency.MONTHLY),
            (["Premium Service", "(annual)"], ItemType.SERVICE_SUBSCRIPTION, SubscriptionFrequency.YEARLY),
            (["Pro Plan", "(yearly)"], ItemType.SOFTWARE_SUBSCRIPTION, SubscriptionFrequency.YEARLY),
            (["Individual Subscription Plan", ""], ItemType.INDIVIDUAL_SUBSCRIPTION, SubscriptionFrequency.UNKNOWN),
            (["Movie Plan", "(monthly)"], ItemType.MOVIE_RENTAL, None),
            (["Movie Plan", "(annual)"], ItemType.MOVIE_PURCHASE, None),
        ],
    )
    def test_determine_subscription_frequency(self, desc_list, item_type, expected_frequency):
        # Create an instance of Item
        item = Item(item_category=ItemCategory.APP, description_list=desc_list,
                    purchase_amount=Decimal("15.00"), other_amount=Decimal("0.00"), image_url="Test URL")
        item.item_type = item_type  # Manually set the item type

        # Assert the subscription frequency determined
        assert item.determine_subscription_frequency(desc_list) == expected_frequency

    @pytest.mark.parametrize(
        "desc_list, item_type, expected_output",
        [
            (["Streaming Plan desc 1", "streaming description"], ItemType.STREAMING_SUBSCRIPTION,
             "Streaming Plan desc 1"),
            (["Service Plan", "Service Subscription"], ItemType.SERVICE_SUBSCRIPTION, "Service Subscription"),
            (["Other Plan", "Other Details"], ItemType.UNKNOWN, "Other Plan"),
        ],
    )
    def test_determine_description_1_returns_expected_output(self, desc_list, item_type, expected_output):
        # Create an instance of Item
        item = Item(item_category=ItemCategory.APP, description_list=desc_list,
                    purchase_amount=Decimal("10.00"), other_amount=Decimal("0.00"), image_url="Test URL")
        item.item_type = item_type  # Manually set the item type to simulate behavior

        # Assert that the method returns the proper description based on item type
        assert item.determine_description_1(desc_list) == expected_output

    @pytest.mark.parametrize(
        "desc_list, item_type, expected_output",
        [
            (["Movie Rental", "HD", "Subtitles"], ItemType.MOVIE_RENTAL, "HD"),
            (["Movie Purchase", "4K", "Subtitles"], ItemType.MOVIE_PURCHASE, "4K"),
            (["In-app Purchase", "Feature", "Extra Content"], ItemType.IN_APP_PURCHASE, "Feature"),
            (["Unknown Plan", "Option1", "Option2"], ItemType.UNKNOWN, "Option1|Option2"),
            (["Streaming Subscription", "Description1"], ItemType.STREAMING_SUBSCRIPTION, None),
        ],
    )
    def test_determine_description_2_returns_expected_output(self, desc_list, item_type, expected_output):
        # Create an instance of Item
        item = Item(item_category=ItemCategory.APP, description_list=desc_list,
                    purchase_amount=Decimal("20.00"), other_amount=Decimal("0.00"), image_url="Test URL")
        item.item_type = item_type  # Manually set the item type to simulate behavior

        # Assert that the method returns the proper description based on item type
        assert item.determine_description_2(desc_list) == expected_output

    @pytest.mark.parametrize(
        "desc_lst, expected_item_type",
        [
            (['Blink Twice', 'Thriller', 'Movie Rental', "Device A"], ItemType.MOVIE_RENTAL),
            (['Heretic', 'Thriller', 'Movie', "Device B"], ItemType.MOVIE_PURCHASE),
            (['Gardenscapes', 'Botanist Kit', 'In-App Purchase', "Device C"], ItemType.IN_APP_PURCHASE),
            (['Max: Stream HBO, TV, & Movies', 'Max Standard Monthly (Monthly)', 'Renews March 24, 2025'], ItemType.STREAMING_SUBSCRIPTION),
            (['Copilot: Track & Budget Money', 'Yearly subscription (Annual)', 'Renews February 12, 2026'], ItemType.SOFTWARE_SUBSCRIPTION),
            (['Premier (Automatic Renewal)', 'Premier (Automatic Renewal) (Monthly)', 'Renews Dec 18, 2024'], ItemType.SERVICE_SUBSCRIPTION),
            (['NYT Games: Word, Number, Logic', 'Games - Annual (Yearly)', 'Renews Sep 24, 2025', "Device G"], ItemType.INDIVIDUAL_SUBSCRIPTION),
            (["Dr. Seuss' How the Grinch Stol", 'In-App Purchase', "Device H"], ItemType.IN_APP_MOVIE_RENTAL),
            (["unknown 1", "unknown 2", "unknown 3", "unknown 4"], ItemType.UNKNOWN),
        ],
    )
    def test_determine_item_type(self, desc_lst, expected_item_type):
        # Create an instance of Item
        item = Item(item_category=ItemCategory.APP, description_list=desc_lst,
                    purchase_amount=Decimal("5.00"), other_amount=Decimal("0.00"), image_url="Test URL")

        # Validate if the correct item type is determined based on description list
        assert item.item_type == expected_item_type


@pytest.fixture
def sample_item_taxable():
    # Returns a sample Item object with initial values
    return Item(
        item_category=ItemCategory.APP,
        description_list=['Gardenscapes', 'Hot Offer', 'In-App Purchase', 'Dawn’s iPad purple'],
        purchase_amount=Decimal("1.99"),
        other_amount=Decimal("1.99"),
        image_url="https://is1-ssl.mzstatic.com/image/thumb/Purple221/v4/80/b0/a1/80b0a143-0270-c6af-18f3-67a2b7c96709/AppIcon-0-0-1x_U007emarketing-0-7-0-85-220.png/128x128bb.jpg",
    )


@pytest.fixture
def sample_item_nontaxable():
    # Returns a sample Item object with initial values
    return Item(
        item_category=ItemCategory.TV,
        description_list=['Blink Twice', 'Thriller', 'Movie Rental', 'Big Daddy’s Apple TV'],
        purchase_amount=Decimal("3.99"),
        other_amount=Decimal("3.99"),
        image_url="https://is1-ssl.mzstatic.com/image/thumb/Purple221/v4/80/b0/a1/80b0a143-0270-c6af-18f3-67a2b7c96709/AppIcon-0-0-1x_U007emarketing-0-7-0-85-220.png/128x128bb.jpg")


def test_apply_tax_when_taxable_true(sample_item_taxable):
    # Apply tax with a positive rate when taxable is True
    tax_rate = Decimal("0.10")
    initial_purchase_amount = sample_item_taxable.purchase_amount

    # Apply tax using the method
    tax_amount = sample_item_taxable.apply_tax(tax_rate)

    # Calculate the expected tax precisely and quantize it like in the method
    expected_tax = (initial_purchase_amount * tax_rate).quantize(Decimal("0.01"), rounding=decimal.ROUND_HALF_UP)

    assert tax_amount == expected_tax
    assert sample_item_taxable.tax_applied == expected_tax
    assert sample_item_taxable.total_amount == initial_purchase_amount + expected_tax


def test_apply_tax_when_taxable_false(sample_item_nontaxable):
    # Apply tax when taxable is False
    tax_rate = Decimal("0.10")

    tax_amount = sample_item_nontaxable.apply_tax(tax_rate)

    assert tax_amount == Decimal("0.00")  # No tax should be applied
    assert sample_item_nontaxable.tax_applied == Decimal("0.00")
    assert sample_item_nontaxable.total_amount == sample_item_nontaxable.purchase_amount


def test_adjust_tax_positive_amount(sample_item_taxable):
    # Adjust tax with a positive adjustment value
    positive_adjustment = Decimal("0.50")
    initial_tax_applied = sample_item_taxable.tax_applied
    initial_total_amount = sample_item_taxable.total_amount

    sample_item_taxable.adjust_tax(positive_adjustment)

    assert sample_item_taxable.tax_applied == initial_tax_applied + positive_adjustment
    assert sample_item_taxable.total_amount == initial_total_amount + positive_adjustment


def test_adjust_tax_negative_amount(sample_item_taxable):
    # Adjust tax with a negative adjustment value
    negative_adjustment = Decimal("-0.50")
    initial_tax_applied = sample_item_taxable.tax_applied
    initial_total_amount = sample_item_taxable.total_amount

    sample_item_taxable.adjust_tax(negative_adjustment)

    assert sample_item_taxable.tax_applied == initial_tax_applied + negative_adjustment
    assert sample_item_taxable.total_amount == initial_total_amount + negative_adjustment
