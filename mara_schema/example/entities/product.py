from mara_schema.entity import Entity, Type

product_entity = Entity(
    name='Product',
    description='Products that were at least once sold or once on stock',
    schema_name='dim')

product_entity.add_attribute(
    name='SKU',
    description='The ID of a product as defined in the PIM system',
    high_cardinality=True,
    column_name='sku',
    type=Type.ID)

from .product_category import product_category_entity

product_entity.link_entity(target_entity=product_category_entity)
