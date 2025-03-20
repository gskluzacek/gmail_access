from decimal import Decimal
from item import Item, ItemCategory, ItemType
from receipt import Receipt


class TestReceipt:
    def setup_method(self):
        # Create test items
        self.item1 = Item(
            item_category=ItemCategory.TV,
            description_list=['Blink Twice', 'Thriller', 'Movie Rental', "Device A"],
            purchase_amount=Decimal("15.00"),
            other_amount=Decimal("0.00"),
            image_url="URL 2",
        )
        self.item2 = Item(
            item_category=ItemCategory.APP,
            description_list=['Clash of Clans', 'Gold Pass', 'In-App Purchase', "Device C"],
            purchase_amount=Decimal("10.00"),
            other_amount=Decimal("0.00"),
            image_url="URL 1"
        )
        self.item3 = Item(
            item_category=ItemCategory.APP,
            description_list=['Gardenscapes', 'Botanist Kit', 'In-App Purchase', "Device C"],
            purchase_amount=Decimal("25.00"),
            other_amount=Decimal("0.00"),
            image_url="URL 3"
        )
        self.item4 = Item(
            item_category=ItemCategory.APP,
            description_list=['Gardenscapes', 'Botanist Kit', 'In-App Purchase', "Device C"],
            purchase_amount=Decimal("25.00"),
            other_amount=Decimal("0.00"),
            image_url="URL 3"
        )
        # Create a receipt
        self.receipt = Receipt(receipt_date="2023-11-01", order_id="123456", doc_nbr="78910",
                               apple_account="test_account", subtotal=Decimal("50.00"), tax=Decimal("4.80"),
                               card="Test Card", total=Decimal("52.80"), file_path="/test/path")
        self.receipt.items = [self.item1, self.item2, self.item3, self.item4]

    def test_apply_tax_to_items_no_adjustment(self):
        expected_item1_tax = Decimal("0.00")
        expected_item2_tax = Decimal("0.80")
        expected_item3_tax = Decimal("2.00")
        expected_item4_tax = Decimal("2.00")

        self.receipt.apply_tax_to_items()
        assert self.item1.tax_applied == expected_item1_tax
        assert self.item2.tax_applied == expected_item2_tax
        assert self.item3.tax_applied == expected_item3_tax
        assert self.item4.tax_applied == expected_item4_tax
        assert sum([expected_item1_tax, expected_item2_tax, expected_item3_tax, expected_item4_tax]) == self.receipt.tax

    def test_apply_tax_to_items_with_adjustment(self):
        self.receipt.tax_rate = Decimal("0.03333333")  # change tax rate so we have a tax adjustment
        self.receipt.tax = Decimal("2.00")  # change the receipt's tax to reflect the new tax rate

        expected_item1_tax = Decimal("0.00")  # however the sum of the taxable items will be 0.01 less than the receipt's tax
        expected_item2_tax = Decimal("0.34")
        expected_item3_tax = Decimal("0.83")
        expected_item4_tax = Decimal("0.83")

        self.receipt.apply_tax_to_items()  # initially the tax applied to the first taxable item will be 0.33 (10.00 * 0.03333333) rounded to 2 decimal places
        assert self.item1.tax_applied == expected_item1_tax
        assert self.item2.tax_applied == expected_item2_tax  # so the first taxable item should be adjusted by 0.01
        assert self.item3.tax_applied == expected_item3_tax
        assert self.item4.tax_applied == expected_item4_tax
        assert sum([expected_item1_tax, expected_item2_tax, expected_item3_tax, expected_item4_tax]) == self.receipt.tax

    def test_add_single_item(self):
        new_item = Item(
            item_category=ItemCategory.APP,
            description_list=['Gardenscapes', 'Botanist Kit', 'In-App Purchase', "Device C"],
            purchase_amount=Decimal("20.00"),
            other_amount=Decimal("0.00"),
            image_url="New URL"
        )
        initial_length = len(self.receipt.items)
        self.receipt.add_item(new_item)
        assert len(self.receipt.items) == initial_length + 1
