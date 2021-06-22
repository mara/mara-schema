from ..data_set import DataSet
from ..entity import Entity

def example_data_sets() -> [DataSet]:
    from .data_sets.customers import customers_data_set
    from .data_sets.order_items import order_items_data_set
    from .data_sets.products import products_data_set
    return [order_items_data_set, customers_data_set, products_data_set]

def example_entities() -> [Entity]:
    from .entities.customer import customer_entity
    from .entities.order import order_entity
    from .entities.order_item import order_item_entity
    from .entities.product import product_entity
    from .entities.product_category import product_category_entity
    return [customer_entity, order_entity, order_item_entity, product_entity, product_category_entity]
