import scrapy
import json
from scrapy.http import FormRequest, Request
from urllib.parse import unquote

class UberEatsSpider(scrapy.Spider):
    name = 'ubereates'
    allowed_domains = ['ubereats.com']

    def __init__(self, location=None, restaurant_url=None, *args, **kwargs):
        super(UberEatsSpider, self).__init__(*args, **kwargs)
        self.location = location
        self.restaurant_url = restaurant_url
        self.uuids_seen = set()
        if not (location and restaurant_url):
            print("Error : Provide the both location or restaurant_url")
        self.restaurant_info = {}
        self.products = []
        self.uuid_of_product = {}
        self.customizations = 0

    def start_requests(self):
        yield FormRequest(
            url="https://www.ubereats.com/_p/api/mapsSearchV1",
            headers={"X-Csrf-Token": "x"},
            formdata={"query": self.location},
            callback=self.parse_result
        )

    def parse_result(self, response):
        data = json.loads(response.text)
        first_place = data.get("data")[0]
        place_id = first_place.get("id")
        provider = first_place.get("provider")

        yield FormRequest(
            url="https://www.ubereats.com/_p/api/getDeliveryLocationV1",
            headers={"X-Csrf-Token": "x"},
            formdata={
                "placeId": place_id,
                "provider": provider,
                "source": "manual_auto_complete"
            },
            callback=self.parse_details
        )

    def parse_details(self, response):
        location_cookie = json.loads(response.text)["data"]
        yield scrapy.Request(
            url=self.restaurant_url,
            callback=self.parse_data,
            cookies={"uev2.loc": json.dumps(location_cookie)}
        )

    def parse_data(self, response):
        uuid = response.css('meta[property="og:url"]::attr(content)').get()
        store_id = uuid.split('/')[-1]

        self.restaurant_info = {
            "Title": response.css("h1::text").get(),
            "Hero Image": response.css('img::attr(src)')[1].get(),
            "Restaurant Location": response.css('p[class*="al"] span[data-testid="rich-text"]::text')[-1].get(),
            "Rating": response.css("span::text")[1].get(),
            "My Location": response.css('div[data-testid="delivery-address-label"]::text').get(),
            "Price Bucket": response.css('p[class*="al"] span[data-testid="rich-text"]::text')[-4].get(),
            "UUID": store_id,
        }

        script = response.css('script[id="__REACT_QUERY_STATE__"]::text').get()
        parsed_script = json.loads(unquote(script.replace("\\u0022", '"')))
        query = parsed_script["queries"][0]
        store_uuid = query["queryKey"][1]["storeUuid"]
        section_uuid = query["state"]["data"]["sections"][0]["uuid"]
        catalog_map = query["state"]["data"]["catalogSectionsMap"]

        for s in catalog_map.values():
            for data in s:
                for item in data['payload']['standardItemsPayload']['catalogItems']:
                    item_id = item.get("uuid")
                    if item_id in self.uuids_seen:
                        continue

                    self.uuids_seen.add(item_id)
                    try:
                        descriptions = item.get("itemDescriptionBadge").get("text")
                    except AttributeError:
                        descriptions = "None"

                    product = {
                        "Title": item.get("title"),
                        "Price": item.get("priceTagline").get("accessibilityText"),
                        "Item Description": descriptions,
                        "Item UUID": item_id,
                        "Product Image URL": item.get("imageUrl"),
                        "Has Customization": item.get("hasCustomizations"),
                    }

                    self.products.append(product)

                    if product["Has Customization"]:
                        self.uuid_of_product[item_id] = product
                        self.customizations += 1

                        yield Request(
                            url="https://www.ubereats.com/_p/api/getMenuItemV1",
                            method="POST",
                            headers={
                                "X-Csrf-Token": "x",
                                "Content-Type": "application/json"
                            },
                            body=json.dumps({
                                "itemRequestType": "ITEM",
                                "storeUuid": store_uuid,
                                "menuItemUuid": item_id,
                                "sectionUuid": section_uuid,
                                "subsectionUuid": item.get("subsectionUuid"),
                                "cbType": "EATER_ENDORSED",
                                "contextReferences": [{"type": "GROUP_ITEMS"}]
                            }),
                            callback=self.parse_customizationlist,
                            meta={
                                "uuid": item_id
                            },
                            dont_filter=True
                        )

        if self.customizations == 0:
            yield self.parse_product_output()

    def clean_customization_data(self, customization):
        keys_to_remove = {"displayState", "groupId", "itemAttributeInfo", "subtitle", "shouldAutoShowChildCustomizations", "minPermittedUnique", "maxPermittedUnique", "subtitleV2"}

        def clean_option(opt):
            for key in list(opt):
                if key in keys_to_remove or opt[key] in [None, [], {}]:
                    opt.pop(key)
            if "childCustomizationList" in opt:
                opt["childCustomizationList"] = [self.clean_customization_data(c) for c in opt["childCustomizationList"]]
            return opt

        for key in list(customization):
            if key in keys_to_remove or customization[key] in [None, [], {}]:
                customization.pop(key)
        if "options" in customization:
            customization["options"] = [clean_option(opt) for opt in customization["options"]]
        return customization

    def parse_customizationlist(self, response):
        uuid = response.meta["uuid"]

        try:
            data = json.loads(response.text)
            customizations = data.get("data", {}).get("customizationsList", [])
            cleaned_customizations = [self.clean_customization_data(c) for c in customizations]

            if uuid in self.uuid_of_product or uuid in self.uuids_seen:
                self.uuid_of_product[uuid]["Customizations"] = cleaned_customizations
        except Exception as error:
            self.logger.error(f"Error parsing customization for {uuid}: {error}")

        self.customizations -= 1
        if self.customizations == 0:
            yield self.parse_product_output()

    def parse_product_output(self):
        return {
            "Restaurant Info": self.restaurant_info,
            "Products": self.products
        }
