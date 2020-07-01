from mara_schema.data_set import DataSet, Aggregation

from ..entities.order_item import order_item_entity

order_items_data_set = DataSet(entity=order_item_entity, name='Order items')

order_items_data_set.include_attributes(['Order', 'Customer', 'Order'], ['Order date'])

order_items_data_set.add_simple_metric(
    name='# Order items',
    description='The number of ordered products',
    column_name='order_item_id',
    aggregation=Aggregation.COUNT)

order_items_data_set.add_simple_metric(
    name='# Orders',
    description='The number of valid orders (orders with an invoice)',
    column_name='order_fk',
    aggregation=Aggregation.DISTINCT_COUNT,
    important_field=True)

order_items_data_set.add_simple_metric(
    name='Product revenue',
    description='The price of the ordered products as shown in the cart',
    aggregation=Aggregation.SUM,
    column_name='product_revenue',
    important_field=True)

order_items_data_set.add_simple_metric(
    name='Shipping revenue',
    description='Revenue generated based on the price of the items and delivery fee',
    aggregation=Aggregation.SUM,
    column_name='shipping_revenue')

order_items_data_set.add_composed_metric(
    name='Revenue',
    description='The total cart value of the order',
    formula='[Product revenue] + [Shipping revenue]',
    important_field=True)

order_items_data_set.add_composed_metric(
    name='AOV',
    description='The average revenue per order. Attention: not meaningful when split by product',
    formula='[Revenue] / [# Orders]',
    important_field=True)
