from mara_schema.data_set import DataSet, Aggregation

from ..entities.customer import customer_entity

customers_data_set = DataSet(entity=customer_entity, name='Customers')

customers_data_set.exclude_path(['Order', 'Customer'])

customers_data_set.add_simple_metric(
    name='# Orders',
    description='Number of orders placed by the customer',
    aggregation=Aggregation.SUM,
    column_name='number_of_orders',
    important_field=True)

customers_data_set.add_simple_metric(
    name='CLV',
    description='The lifetime revenue generated from items purchased by this customer',
    aggregation=Aggregation.SUM,
    column_name='revenue_lifetime',
    important_field=True)

customers_data_set.add_composed_metric(
    name='AOV',
    description='The average revenue per order of the customer',
    formula='[CLV] / [# Orders]')
