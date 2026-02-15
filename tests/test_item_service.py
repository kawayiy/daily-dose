
from app.services.item_service import ItemService

"""
Tests for ItemService. Uses the app_context fixture from tests/conftest.py.
Run: 
1. Run all tests in this file with verbose output
python -m pytest tests/test_item_service.py -v
2. Run only the test_add_item_returns_item_with_id test with verbose output
python -m pytest tests/test_item_service.py::test_add_item_returns_item_with_id -v
"""


def test_add_item_returns_item_with_id(app_context):
    """add_item(name) returns an Item with id and name."""
    item = ItemService.add_item("service-test-name")
    assert item.id is not None
    assert item.name == "service-test-name"

def test_get_all_items_returns_list_of_dicts(app_context):
    """get_all_items() returns a list of dicts with id and name."""
    ItemService.add_item("list-test-item")
    data = ItemService.get_all_items()
    print("response result: ", data)
    assert isinstance(data, list)
    assert len(data) >= 1
    for row in data:
        assert "id" in row and "name" in row
        assert isinstance(row["id"], int)
        assert isinstance(row["name"], str)

def test_add_item_then_get_all_includes_it(app_context):
    """After add_item, get_all_items() includes the new item."""
    name = "unique-check-item"
    ItemService.add_item(name)
    all_items = ItemService.get_all_items()
    names = [r["name"] for r in all_items]
    assert name in names