from mara_schema.attribute import Type
from mara_schema.entity import Entity

customer_entity = Entity(
    name='Customer',
    description='People that made at least one order or that subscribed to the newsletter',
    schema_name='dim')

customer_entity.add_attribute(
    name='Customer ID',
    description='The ID of the customer as defined in the backend',
    column_name='customer_id',
    type=Type.ID,
    high_cardinality=True,
    important_field=True)

customer_entity.add_attribute(
    name='Email',
    description='The email of the customer',
    column_name='email',
    personal_data=True,
    high_cardinality=True,
    accessible_via_entity_link=False)

customer_entity.add_attribute(
    name='Duration since first order',
    description='The number of days since the first order was placed',
    type=Type.DURATION,
    column_name='duration_since_first_order',
    accessible_via_entity_link=False)

from .order import order_entity
from .product_category import product_category_entity

customer_entity.link_entity(
    target_entity=product_category_entity,
    fk_column='favourite_product_category_fk',
    prefix='Favourite product category',
    description='The category of the most purchased product (by revenue) of the customer')

customer_entity.link_entity(
    target_entity=order_entity,
    fk_column='first_order_fk',
    prefix='First order')
