
from app import db
from app.models.demo import Item

class ItemService:
    """Item-related business logic."""

    @staticmethod
    def add_item(name: str) -> Item:
        '''Create and persist an item with the given name. Returns the created Item.'''
        item = Item(name=name)
        db.session.add(item)
        db.session.commit()
        return item

    @staticmethod
    def get_all_items() -> list[dict]:
        '''Return all items as a list of dicts with 'id' and 'name'.'''
        items = Item.query.all()
        return [{'id': i.id, 'name': i.name } for i in items] 