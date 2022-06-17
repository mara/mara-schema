# Mara Schema

[![Build Status](https://github.com/mara/mara-schema/actions/workflows/build.yaml/badge.svg)](https://github.com/mara/mara-schema/actions/workflows/build.yaml)
[![PyPI - License](https://img.shields.io/pypi/l/mara-schema.svg)](https://github.com/mara/mara-schema/blob/main/LICENSE)
[![PyPI version](https://badge.fury.io/py/mara-schema.svg)](https://badge.fury.io/py/mara-schema)
[![Slack Status](https://img.shields.io/badge/slack-join_chat-white.svg?logo=slack&style=social)](https://communityinviter.com/apps/mara-users/public-invite)

Python based mapping of physical data warehouse tables to logical business entities (a.k.a. "cubes", "models", "data sets", etc.). It comes with 
- sql query generation for flattening normalized database tables into wide tables for various analytics front-ends
- a flask based visualization of the schema that can serve as a documentation of the business definitions of a data warehouse (a.k.a "data dictionary" or "data guide")
- the possibility to sync schemas to reporting front-ends that have meta-data APIs (e.g. Metabase, Looker, Tableau)    

&nbsp;

![Mara Schema overview](https://github.com/mara/mara-schema/raw/main/docs/_static/mara-schema.png)

&nbsp;

Have a look at a real-world application of Mara Schema in the [Mara Example Project 1](https://github.com/mara/mara-example-project-1).

&nbsp;

**Why** should I use Mara Schema?

1. **Definition of analytical business entities as code**: There are many solutions for documenting the company-wide definitions of attributes & metrics for the users of a data warehouse. These can range from simple spreadsheets or wikis to metadata management tools inside reporting front-ends. However, these definitions can quickly get out of sync when new columns are added or changed in the underlying data warehouse. Mara Schema allows to deploy definition changes together with changes in the underlying ETL processes so that all definitions will always be in sync with the underlying data warehouse schema.


2. **Automatic generation of aggregates / artifacts**: When a company wants to enforce a *single source of truth* in their data warehouse, then a heavily normalized Kimball-style [snowflake schema](https://en.wikipedia.org/wiki/Snowflake_schema) is still the weapon of choice. It enforces an agreed-upon unified modelling of business entities across domains and ensures referential consistency. However, snowflake schemas are not ideal for analytics or data science because they require a lot of joins. Most analytical databases and reporting tools nowadays work better with pre-flattened wide tables. Creating such flattened tables is an error-prone and dull activity, but with Mara Schema one can automate most of the work in creating flattened data set tables in the ETL.
 
&nbsp;

## Installation

To use the library directly, use pip:

```
pip install mara-schema
```

or
 
```
pip install git+https://github.com/mara/mara-schema.git
```

&nbsp;

## Defining entities, attributes, metrics & data sets

Let's consider the following toy example of a dimensional schema in the data warehouse of a hypothetical e-commerce company:

![Example dimensional star schema](https://github.com/mara/mara-schema/raw/main/docs/_static/example-dimensional-database-schema.svg)

Each box is a database table with its columns, and the lines between tables show the foreign key constraints. That's a classic Kimball style [snowflake schema](https://en.wikipedia.org/wiki/Snowflake_schema) and it requires a proper modelling / ETL layer in your data warehouse. A script that creates these example tables in PostgreSQL can be found in [example/dimensional-schema.sql](https://github.com/mara/mara-schema/blob/main/mara_schema/example/dimensional-schema.sql).

It's a prototypical data warehouse schema for B2C e-commerce: There are orders composed of individual product purchases (order items) made by customers. There are circular references: Orders have a customer, and customers have a first order. Order items have a product (and thus a product category) and customers have a favourite product category.

The respective entity and data set definitions for this database schema can be found in the [mara_schema/example](https://github.com/mara/mara-schema/tree/main/mara_schema/example) directory.

&nbsp;

In Mara Schema, each business relevant table in the dimensional schema is mapped to an [Entity](https://github.com/mara/mara-schema/blob/main/mara_schema/entity.py). In dimensional modelling terms, entities can be both fact tables and dimensions. For example, a customer entity can be a dimension of an order items data set (a.k.a. "cube", "model", "data mart") and a customer data set of its own.

Here's a [shortened](https://github.com/mara/mara-schema/blob/main/mara_schema/example/entities/order_item.py) defnition of the "Order item" entity based on the `dim.order_item` table:

```python
from mara_schema.entity import Entity

order_item_entity = Entity(
    name='Order item',
    description='Individual products sold as part of an order',
    schema_name='dim')
```

It assumes that there is an `order_item` table in the `dim` schema of the data warehouse, with `order_item_id` as the primary key. The optional `table_name` and `pk_column_name` parameters can be used when another naming scheme for tables and primary keys is used.  

&nbsp;

[Attributes](https://github.com/mara/mara-schema/blob/main/mara_schema/attribute.py) represent facts about an entity. They correspond to the non-numerical columns in a fact or dimension table: 

```python
from mara_schema.attribute import Type

order_item_entity.add_attribute(
    name='Order item ID',
    description='The ID of the order item in the backend',
    column_name='order_item_id',
    type=Type.ID,
    high_cardinality=True)
```

They come with a speaking name (as shown in reporting front-ends), a description and a `column_name` in the underlying database table. 

There a several parameters for controlling the generation of artifact tables and the visibility in front-ends: 
- Setting `personal_data` to `True` means that the attribute contains personally identifiable information and thus should be hidden from most users.
- When `high_cardinality` is `True`, then the attribute is hidden in front-ends that can not deal well with dimensions with a lot of values.
- The `type` attribute controls how some fields are treated in artifact creation. See [mara_schema/attribute.py#L7](https://github.com/mara/mara-schema/blob/main/mara_schema/attribute.py#L7).
- An `important_field` highlights the data set and is shown by default in overviews.
- When `accessible_via_entity_link` is `False`, then the attribute will be hidden in data sets that use the entity as an dimension.

&nbsp;

The attributes of the dimensions of an entity are recursively linked with the `link_entity` method:

```python
from .order import order_entity
from .product import product_entity

order_item_entity.link_entity(target_entity=order_entity, prefix='')
order_item_entity.link_entity(target_entity=product_entity)
```

This pulls in attributes of other entities that are connected to an entity table via foreign key columns. When the other entity is called "Foo bar", then it's assumed that there is a `foo_bar_fk` in the entity table (can be overwritten with the `fk_column` parameter). The optional `prefix` controls how linked attributes are named (e.g. "First order date" vs "Order date") and also helps to disambiguate when there are multiple links from one entity to another.

&nbsp;

Once all entities and their relationships are established, [Data Sets](https://github.com/mara/mara-schema/blob/main/mara_schema/data_set.py) (a.k.a "cubes", "models" or "data marts") add metrics and attributes from linked entities to an entity:

```python
from mara_schema.data_set import DataSet

from ..entities.order_item import order_item_entity

order_items_data_set = DataSet(entity=order_item_entity, name='Order items')
```

&nbsp;

There are two kinds of [Metrics](https://github.com/mara/mara-schema/blob/main/mara_schema/metric.py) (a.k.a "Measures") in Mara Schema: simple metrics and composed metrics. Simple metrics are computed as direct aggregations on an entity table column: 

```python
from mara_schema.data_set import Aggregation

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
```

In this example the metric "# Orders" is defined as the distinct count on the `order_fk` column, and "Product revenue" as the sum of the `product_revenue` column.

Composed metrics are built from other metrics (both simple and composed)  like this:  

```python
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
```   

The `formula` parameter takes simple algebraic expressions (`+`, `-`, `*`, `/` and parentheses) with the names of the parent metrics in rectangular brackets, e.g. `([a] + [b]) / [c]`.

&nbsp;

With complex snowflake schemas the graph of linked entities can become rather big. To avoid cluttering data sets with unnecessary attributes, Mara Schema has a way for excluding entire entity links:

```python
customers_data_set.exclude_path(['Order', 'Customer'])
```

This means that the customer of the first order of a customer will not be part of the customers data set. Similarly, it is possible to limit the list of attributes from a linked entity: 

```python
order_items_data_set.include_attributes(['Order', 'Customer', 'Order'], ['Order date'])
```

Here only the order date of the first order of the customer of the order will be included in the data set.  
 
&nbsp;

## Visualization

Mara schema comes with (an optional) Flask based visualization that documents the metrics and attributes of all data sets:

![Mara schema data set visualization](https://github.com/mara/mara-schema/raw/main/docs/_static/mara-schema-data-set-visualization.png)

When made available to business users, then this can serve as the "data dictionary", "data guide" or "data catalog" of a company. 

&nbsp;

## Artifact generation

The function `data_set_sql_query` in [mara_schema/sql_generation.py](https://github.com/mara/mara-schema/blob/main/mara_schema/sql_generation.py) can be used to flatten the entities of a data set into a wide data set table: 

```python
data_set_sql_query(data_set=order_items_data_set, human_readable_columns=True, pre_computed_metrics=False,
                   star_schema=False, personal_data=False, high_cardinality_attributes=True)
```

The resulting SELECT statement can be used for creating a data set table that is specifically tailored for the use in Metabase:

```sql
SELECT
     order_item.order_item_id AS "Order item ID",

    "order".order_id AS "Order ID",
    "order".order_date AS "Order date",

    order_customer.customer_id AS "Customer ID",

    order_customer_favourite_product_category.main_category AS "Customer favourite product category level 1",
    order_customer_favourite_product_category.sub_category_1 AS "Customer favourite product category level 2",

    order_customer_first_order.order_date AS "Customer first order date",

    product.sku AS "Product SKU",

    product_product_category.main_category AS "Product category level 1",
    product_product_category.sub_category_1 AS "Product category level 2",

    order_item.order_item_id AS "# Order items",
    order_item.order_fk AS "# Orders",
    order_item.product_revenue AS "Product revenue",
    order_item.revenue AS "Shipping revenue"

FROM dim.order_item order_item
LEFT JOIN dim."order" "order" ON order_item.order_fk = "order".order_id
LEFT JOIN dim.customer order_customer ON "order".customer_fk = order_customer.customer_id
LEFT JOIN dim.product_category order_customer_favourite_product_category ON order_customer.favourite_product_category_fk = order_customer_favourite_product_category.product_category_id
LEFT JOIN dim."order" order_customer_first_order ON order_customer.first_order_fk = order_customer_first_order.order_id
LEFT JOIN dim.product product ON order_item.product_fk = product.product_id
LEFT JOIN dim.product_category product_product_category ON product.product_category_fk = product_product_category.product_category_id
```

Please note that the `data_set_sql_query` only returns SQL select statements, it's a matter of executing these statements somewhere in the ETL of the Data Warehouse. [Here](https://github.com/mara/mara-example-project-1/tree/main/app/pipelines/generate_artifacts/metabase.py) is an example for creating data set tables for Metabase using [Mara Pipelines](https://github.com/mara/mara-pipelines).

&nbsp;

There are several parameters for controlling the output of the `data_set_sql_query` function:

 - `human_readable_columns`: Whether to use "Customer name" rather than "customer_name" as column name
 - `pre_computed_metrics`: Whether to pre-compute composed metrics, counts and distinct counts on row level
 - `star_schema`: Whether to add foreign keys to the tables of linked entities rather than including their attributes
 - `personal_data`: Whether to include attributes that are marked as personal data
 - `high_cardinality_attributes`: Whether to include attributes that are marked to have a high cardinality

![Mara schema SQL generation](https://github.com/mara/mara-schema/raw/main/docs/_static/mara-schema-sql-generation.gif)


## Schema sync to front-ends

When reporting tools have a Metadata API (e.g. Metabase, Tableau) or can read schema definitions from text files (e.g. Looker, Mondrian), then it's easy to sync definitions with them. The [Mara Metabase](https://github.com/mara/mara-metabase) package contains a function for syncing Mara Schema definitions with Metabase and the [Mara Mondrian](https://github.com/mara/mara-mondrian) package contains a generator for a Mondrian schema.

We welcome contributions for creating Looker LookML files, for syncing definitions with Tableau, and for syncing with any other BI front-end.

Also, we see a potential for automatically creating data guides in other Wikis or documentation tools.


## Installation

To use the library directly, use pip:

```
pip install mara-schema
```

or
 
```
pip install git+https://github.com/mara/mara-schema.git
```

For an example of an integration into a flask application, have a look at the [Mara Example Project 1](https://github.com/mara/mara-example-project-1).

&nbsp;

## Links

* Documentation: https://mara-schema.readthedocs.io/
* Changes: https://mara-schema.readthedocs.io/en/stable/changes.html
* PyPI Releases: https://pypi.org/project/mara-schema/
* Source Code: https://github.com/mara/mara-schema
* Issue Tracker: https://github.com/mara/mara-schema/issues
