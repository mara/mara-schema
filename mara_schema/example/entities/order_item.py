from mara_schema.attribute import Type
from mara_schema.entity import Entity

order_item_entity = Entity(
    name='Order item',
    description='Individual products sold as part of an order',
    schema_name='dim')

order_item_entity.add_attribute(
    name='Order item ID',
    description='The ID of the order item in the backend',
    column_name='order_item_id',
    type=Type.ID,
    high_cardinality=True)

from .order import order_entity
from .product import product_entity

order_item_entity.link_entity(target_entity=order_entity, prefix='')
order_item_entity.link_entity(target_entity=product_entity)
