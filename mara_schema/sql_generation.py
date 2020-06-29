import re

import sqlalchemy
import sqlalchemy.engine

from .attribute import Type, normalize_name
from .data_set import DataSet
from .entity import EntityLink
from .metric import SimpleMetric, Aggregation


def data_set_sql_query(data_set: DataSet,
                       human_readable_columns=True,
                       pre_computed_metrics=True,
                       star_schema: bool = False,
                       personal_data=True,
                       high_cardinality_attributes=True,
                       engine: sqlalchemy.engine.Engine = None) -> str:
    """
    Returns a SQL select statement that flattens all linked entities of a data set into a wide table

    Args:
        data_set: the data set to flatten
        human_readable_columns: Whether to use "Customer name" rather than "customer_name" as column name
        pre_computed_metrics: Whether to pre-compute composed metrics, counts and distinct counts on row level
        star_schema: Whether to add foreign keys to the tables of linked entities rather than including their attributes
        personal_data: Whether to include attributes that are marked as personal data
        high_cardinality_attributes: Whether to include attributes that are marked to have a high cardinality
        engine: A sqlalchemy engine that is used to quote database identifiers. Defaults to a PostgreSQL engine.

    Returns:
        A string containing the select statement
    """
    engine = engine or sqlalchemy.create_engine(f'postgresql+psycopg2://')

    def quote(name) -> str:
        """Quote a column or table name for the specified database engine"""
        return engine.dialect.identifier_preparer.quote(name)

    # alias for the underlying table of the entity of the data set
    entity_table_alias = database_identifier(data_set.entity.name)

    # progressively build the query
    query = 'SELECT'

    column_definitions = []

    # Iterate all connected entities
    for path, attributes in data_set.connected_attributes().items():
        first = True  # for adding an empty line between each entity

        # helper function for adding a column
        def add_column_definition(table_alias: str, column_name: str, column_alias: str,
                                  cast_to_text: bool, first: bool, custom_column_expression: str = None):
            column_definition = '\n    ' if first else '    '
            column_definition += custom_column_expression or f'{quote(table_alias)}.{quote(column_name)}'
            if cast_to_text:
                column_definition += '::TEXT'
            if column_alias != column_name:
                column_definition += f' AS {quote(column_alias)}'
            column_definitions.append(column_definition)

            return False

        if star_schema and path:  # create a foreign key to the last entity of the path
            first = add_column_definition(
                table_alias=table_alias_for_path(path[:-1]) if len(path) > 1 else entity_table_alias,
                column_name=path[-1].fk_column,
                column_alias=(normalize_name(' '.join([entity_link.prefix or entity_link.target_entity.name
                                                       for entity_link in path]))
                              if human_readable_columns else table_alias_for_path(path) + '_fk'),
                cast_to_text=False, first=first)

        # Add columns for all attributes
        for name, attribute in attributes.items():
            if attribute.personal_data and not personal_data:
                continue
            if attribute.high_cardinality and not high_cardinality_attributes:
                continue

            table_alias = table_alias_for_path(path) if path else entity_table_alias
            column_name = attribute.column_name
            column_alias = name if human_readable_columns else database_identifier(name)
            custom_column_expression = None

            if star_schema:  # Add foreign keys for dates and durations
                if attribute.type == Type.DATE:
                    custom_column_expression = f"TO_CHAR({quote(table_alias)}.{quote(column_name)}, 'YYYYMMDD') :: INTEGER"
                    column_alias = name if human_readable_columns else database_identifier(name) + '_fk'
                elif attribute.type == Type.DURATION:
                    column_alias = name if human_readable_columns else database_identifier(name) + '_fk'
                elif not path:
                    pass  # Add attributes of data set entity
                else:
                    continue  # Exclude attributes from linked entities

            first = add_column_definition(table_alias=table_alias, column_name=column_name, column_alias=column_alias,
                                          cast_to_text=attribute.type == Type.ENUM, first=first,
                                          custom_column_expression=custom_column_expression)

    # helper function for pre-computing composed metrics
    def sql_formula(metric):
        if isinstance(metric, SimpleMetric):
            if metric.aggregation in [Aggregation.DISTINCT_COUNT, Aggregation.COUNT]:
                # for distinct counts, return 1::SMALLINT if the expression is not null
                return f'({quote(entity_table_alias)}.{quote(metric.column_name)} IS NOT NULL) ::INTEGER :: SMALLINT'
            else:
                # Coalesce with 0 so that metrics that combine simplemetrics work ( in SQL `1 + NULL` is `NULL` )
                return f'COALESCE({quote(entity_table_alias)}.{quote(metric.column_name)}, 0)'
        else:
            if '/' in metric.formula_template:  # avoid divisions by 0
                return metric.formula_template.format(
                    *[f'(NULLIF({sql_formula(metric)}, 0.0))' for metric in metric.parent_metrics])

            else:  # render metric template
                return metric.formula_template.format(
                    *[f'({sql_formula(metric)})' for metric in metric.parent_metrics])

    first = True
    for name, metric in data_set.metrics.items():
        column_alias = metric.name if human_readable_columns else database_identifier(metric.name)

        if pre_computed_metrics:
            column_definition = f'    {sql_formula(metric)} AS {quote(column_alias)}'
        elif isinstance(metric, SimpleMetric):
            column_definition = f'    {quote(entity_table_alias)}.{quote(metric.column_name)}'
            if column_alias != metric.column_name:
                column_definition += f' AS {quote(column_alias)}'
        else:
            continue

        if first:
            column_definition = '\n' + column_definition
            first = False
        column_definitions.append(column_definition)

    # add column definitions to SELECT part
    query += ',\n'.join(column_definitions)

    # add FROM part for entity table
    query += f'\n\nFROM {quote(data_set.entity.schema_name)}.{quote(data_set.entity.table_name)} {quote(entity_table_alias)}'

    # Add LEFT JOIN statements
    for path in data_set.paths_to_connected_entities():
        left_alias = table_alias_for_path(path[:-1]) if len(path) > 1 else database_identifier(data_set.entity.name)
        right_alias = table_alias_for_path(path)
        entity_link = path[-1]
        target_entity = entity_link.target_entity

        query += f'\nLEFT JOIN {quote(target_entity.schema_name)}.{quote(target_entity.table_name)} {quote(right_alias)}'
        query += f' ON {quote(left_alias)}.{quote(path[-1].fk_column)} = {quote(right_alias)}.{quote(target_entity.pk_column_name)}'

    return query


def database_identifier(name) -> str:
    """Turns a string into something that can be used as a table or column name"""
    return re.sub('[^0-9a-z]+', '_', name.lower())


def table_alias_for_path(path: (EntityLink,)) -> str:
    """Turns `(<EntityLink 'Customer'>, <EntityLink 'First order'>,)` into `customer_first_order` """
    return database_identifier('_'.join([entity_link.prefix or entity_link.target_entity.name
                                         for entity_link in path]))
