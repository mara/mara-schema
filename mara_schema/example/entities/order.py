from mara_schema.attribute import Type
from mara_schema.entity import Entity

order_entity = Entity(
    name='Order',
    description='Valid orders for which an invoice was created',
    schema_name='dim')

order_entity.add_attribute(
    name='Order ID',
    description='The invoice number of the order as stored in the backend',
    column_name='order_id',
    type=Type.ID,
    important_field=True,
    high_cardinality=True)

order_entity.add_attribute(
    name='Order date',
    description='The date when the order was placed (stored in the backend)',
    column_name='order_date',
    type=Type.DATE,
    important_field=True)

order_entity.add_attribute(
    name='Status',
    description='The current status of the order (new, paid, shipped, etc.)',
    column_name='status',
    accessible_via_entity_link=False,
    type=Type.ENUM)

from .customer import customer_entity

order_entity.link_entity(
    target_entity=customer_entity,
    description='The customer who placed the order')
