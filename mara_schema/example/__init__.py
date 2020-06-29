from ..data_set import DataSet


def example_data_sets() -> [DataSet]:
    from .data_sets.customers import customers_data_set
    from .data_sets.order_items import order_items_data_set
    from .data_sets.products import products_data_set
    return [order_items_data_set, customers_data_set, products_data_set]
