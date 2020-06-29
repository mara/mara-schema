from mara_schema.data_set import DataSet, Aggregation

from ..entities.product import product_entity

products_data_set = DataSet(entity=product_entity, name='Products')

products_data_set.add_simple_metric(
    name='Revenue last 30 days',
    description='The revenue generated from the product in the last 30 days',
    aggregation=Aggregation.SUM,
    column_name='revenue_last_30_days',
    important_field=True)

products_data_set.add_simple_metric(
    name='# Items on stock',
    description='How many items of the products are in stock according to the ERP (at the time of the last DWH import)',
    column_name='number_of_items_on_stock',
    aggregation=Aggregation.SUM,
    important_field=True)
