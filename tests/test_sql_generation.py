from mara_schema.sql_generation import sql_for_flattened_table, sql_for_mondrian_fact_table
from .conftest import mock_data_sets


def normalize(str):
    """Normalize the string in order to produce the same output for testing."""
    import re
    return re.sub(' ', '', re.sub(r'\s+', r' ', str)).lower()


def test_sql_for_flattened_table(mock_data_sets):
    _data_set = next((data_set for data_set in mock_data_sets if data_set.name == 'Order items'), None)
    sql = sql_for_flattened_table(_data_set)
    expected_sql = """
SELECT "Order item".order_item_id  AS "Order item ID",
    "Order".order_date  AS "Order date",
    "Order".status :: TEXT AS "Status",
    "Customer".age  AS "Age",
    "Product".categories  AS "Categories"
,    COALESCE("Order item".revenue, 0) AS "Revenue"
FROM e_dim.order_item "Order item" 
LEFT JOIN e_dim.order "Order" ON "Order item".order_fk = "Order".order_id 
LEFT JOIN e_dim.customer "Customer" ON "Order".customer_fk = "Customer".customer_id 
LEFT JOIN e_dim.product "Product" ON "Order item".product_fk = "Product".product_id
"""

    assert normalize(sql) == normalize(expected_sql)


def test_sql_for_mondrian_fact_table(mock_data_sets):
    _data_set = next((data_set for data_set in mock_data_sets if data_set.name == 'Order items'), None)
    sql = sql_for_mondrian_fact_table(_data_set)
    expected_sql = """
CREATE TABLE af_dim_next.order_item_fact AS
SELECT  "Order item".order_item_id ,
     "Order item".revenue ,
    "Order item".order_fk AS "Order item order_fk",
     TO_CHAR("Order".order_date, 'YYYYMMDD') :: INTEGER AS         "Order date (FK)" ,
    "Order".customer_fk AS "Order customer_fk",
    "Order item".product_fk AS "Order item product_fk" 
FROM e_dim.order_item "Order item" 
LEFT JOIN e_dim.order "Order" ON "Order item".order_fk = "Order".order_id 
LEFT JOIN e_dim.customer "Customer" ON "Order".customer_fk = "Customer".customer_id 
LEFT JOIN e_dim.product "Product" ON "Order item".product_fk = "Product".product_id 
"""

    assert normalize(sql) == normalize(expected_sql)


