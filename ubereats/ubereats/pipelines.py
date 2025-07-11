from scrapy.exceptions import DropItem

class JsonWriterPipeline:
    def process_item(self, item, spider):
        return item

class DuplicatesPipeline:
    def __init__(self):
        self.ids_seen = set()
    def process_item(self, item, spider):
        item_id = item.get("id")
        if item_id in self.ids_seen:
            raise DropItem(f"Duplicate item found: {item_id}")
        else:
            self.ids_seen.add(item_id)
            return item