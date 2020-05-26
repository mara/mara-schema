import collections
import typing

from mara_schema import config
from mara_schema.schema import DataSet, Entity, Type, SimpleMetric
from mara_schema.schema import paths_to_connected_entities, generate_attribute_name, \
    normalize_name


def sql_for_flattened_table(data_set: DataSet) -> str:
    """Returns a SQL select statement to create a flattened table based on a `DataSet` configuration"""

    def column_definition_for_attribute(table_alias: str,
                                        column_name: str,
                                        attribute_name: str,
                                        type_casting: str):
        return f'"{table_alias}".{column_name} {type_casting} AS "{attribute_name}"'

    def generate_attribute_query(entity: Entity) -> str:

        result = []

        query_elements_attributes = []

        QueryElementsAttribute = collections.namedtuple('QueryElementsAttribute',
                                                        ['table_alias', 'column_name', 'attribute_name',
                                                         'type_casting'])
        for path, attributes in data_set.connected_attributes().items():
            if not path:
                for attribute in attributes:
                    name = generate_attribute_name(attribute)
                    query_elements_attribute = QueryElementsAttribute(entity.name, attribute.column_name, name,
                                                                      ':: TEXT' if attribute.type == Type.ENUM else '')
                    query_elements_attributes.append(query_elements_attribute)
            else:
                entity = path[-1].target_entity

                for attribute in attributes:
                    table_alias = generate_table_alias(path)
                    name = generate_attribute_name(attribute, path)
                    query_elements_attribute = QueryElementsAttribute(table_alias, attribute.column_name, name,
                                                                      ':: TEXT' if attribute.type == Type.ENUM else '')
                    query_elements_attributes.append(query_elements_attribute)

        for query_elements_attribute in query_elements_attributes:
            column_definition = column_definition_for_attribute(
                table_alias=query_elements_attribute.table_alias,
                column_name=query_elements_attribute.column_name,
                attribute_name=query_elements_attribute.attribute_name,
                type_casting=query_elements_attribute.type_casting)
            result.append(column_definition)

        return ',\n    '.join(result)

    def generate_metrics_query(data_set):
        sql_metrics = []
        for name, metric in data_set.metrics.items():
            sql_metrics.append(f'{metric.sql_formula()} AS "{name}"')

        return ',\n    '.join(sql_metrics)

    query = f"""
SELECT {generate_attribute_query(data_set.entity)}"""

    if len(data_set.metrics) > 0:
        query += f"""\n,    {generate_metrics_query(data_set)}"""

    query += f"""
{ _build_sql_join(data_set=data_set)}
"""

    return query


def sql_for_mondrian_fact_table(data_set: DataSet) -> str:
    """
    Returns a SQL create table statement to create a mondrian fact table based on a `DataSet` configuration.
    Args:
        data_set: An DataSet object.
    Returns:
        A SQL create table statement.
    """

    def attributes_metrics_sql(data_set: DataSet) -> []:

        result = set()
        table_alias = data_set.entity.name
        for attribute in data_set.entity.attributes:
            if attribute.type not in [Type.DATE, Type.DURATION]:
                result.add(f""" "{table_alias}".{attribute.column_name} """)

        for name, metric in data_set.metrics.items():
            if isinstance(metric, SimpleMetric):
                result.add(f""" "{table_alias}".{metric.column_name} """)

        return list(result)

    def foreign_keys_sql(data_set):

        result = []

        table_alias = data_set.entity.name

        for attribute in data_set.entity.attributes:
            if attribute.type in config.mondrian_dimension_templates():
                if attribute.type == Type.DATE:
                    result.append(
                        f""" TO_CHAR("{table_alias}".{attribute.column_name}, 'YYYYMMDD') :: INTEGER AS \
    "{generate_fk_from_attribute(attribute)}" """)
                elif attribute.type == Type.DURATION:
                    result.append(
                        f""" "{table_alias}".{attribute.column_name} AS \
    "{generate_fk_from_attribute(attribute)}" """)

        for path, attributes in data_set.connected_attributes().items():
            if path:
                if len(path) > 1:
                    table_alias = generate_table_alias(path[:-1])
                else:
                    table_alias = data_set.entity.name

                result.append(
                    f'"{table_alias}".{path[-1].fk_column} AS "{generate_mondrian_fact_table_fk(data_set, path)}"')

                table_alias = generate_table_alias(path)

                for attribute in attributes:
                    if attribute.type in config.mondrian_dimension_templates():
                        if attribute.type == Type.DATE:
                            result.append(
                                f""" TO_CHAR("{table_alias}".{attribute.column_name}, 'YYYYMMDD') :: INTEGER AS \
        "{generate_fk_from_attribute(attribute, path)}" """)
                        elif attribute.type == Type.DURATION:
                            result.append(
                                f""" "{table_alias}".{attribute.column_name} AS \
            "{generate_fk_from_attribute(attribute, path)}" """)

        return result

    target_schema = config.mondrian_schema()["fact_table_schema_name"]

    attributes_and_metrics = attributes_metrics_sql(data_set)
    foreign_keys = foreign_keys_sql(data_set)

    all_columns = ',\n    '.join(attributes_and_metrics + foreign_keys)

    query = f"""
CREATE TABLE {target_schema}_next.{data_set.entity.table_name}_fact AS
SELECT {all_columns} """
    query += f"""
{ _build_sql_join(data_set)}
"""
    return query


def sql_for_metabase_fact_table():
    pass


def _build_sql_join(data_set: DataSet, join_entity_only_when_entity_links_exists: bool = False) -> str:
    """
    Generate sql from- and join-clauses.
    """

    join_statement = list()

    join_statement.append(
        f"""FROM {data_set.entity.schema_name}.{data_set.entity.table_name} "{data_set.entity.name}" """)

    paths = paths_to_connected_entities(data_set=data_set)

    for entity_links in paths:

        table_alias_for_right_table = generate_table_alias(entity_links)

        if len(entity_links) == 1:
            table_alias_for_left_table = data_set.entity.name
        else:
            table_alias_for_left_table = generate_table_alias(entity_links[:-1])

        target_entity = entity_links[-1].target_entity

        join = f"""LEFT JOIN {target_entity.schema_name}.{target_entity.table_name} "{table_alias_for_right_table}" \
ON "{table_alias_for_left_table}".{entity_links[-1].fk_column} \
= "{table_alias_for_right_table}".{target_entity.pk_column_name} """

        if join_entity_only_when_entity_links_exists:
            if len(target_entity.entity_links) > 0:
                join_statement.append(join)
        else:
            join_statement.append(join)
    return '\n'.join(join_statement)


def generate_table_alias(path: typing.Tuple[Entity.EntityLink]) -> str:
    """Generate a table alias by concatenating the prefix of entity link instances and target entity name, e.g. "First
    Booking". """
    table_alias = ' '.join([entity_link.prefix for entity_link in path]) + ' ' + path[-1].target_entity.name
    return normalize_name(table_alias)


def generate_mondrian_fact_table_fk(data_set: DataSet, path: typing.Tuple[Entity.EntityLink] = None):
    """Generate the foreign key column for mondrian fact table, e.g. "First booking booking_fk" """
    if len(path) > 1:
        return generate_table_alias(path[:-1]) + ' ' + path[-1].fk_column
    elif len(path) == 1:
        return data_set.entity.name + ' ' + path[0].fk_column


def generate_fk_from_attribute(attribute: Entity.Attribute, path: typing.Tuple[Entity.EntityLink] = None):
    """Generate the foreign key column from attribute column, e.g. "First booking date (FK)". """
    suffix = ' (FK)'
    if path:
        return generate_attribute_name(attribute, path) + suffix
    else:
        return generate_attribute_name(attribute) + suffix
