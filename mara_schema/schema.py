import abc
import enum
import re
import typing


class Entity():
    def __init__(self, name: str, description: str,
                 schema_name: str, table_name: str = None,
                 pk_column_name: str = None):
        """
        A business object with attributes and links to other entities, corresponds to a table in the dimensional schema
        Args:
            name: A short noun phrase that captures the nature of the entity.  E.g. "Customer", "Order item"
            description: A short text that helps to understand the underlying business process.
                E.g. "People who registered through the web site or installed the app"
            schema_name: The database schema of the underlying table in the dimensional schema, e.g. "xy_dim"
            table_name: The name of the underlying table in the dimensional schema, e.g. "order_item".
                Defaults to the lower-cased entity name with spaces replaced by underscores
            pk_column_name: The primary key column in the underlying table, defaults to table_name + '_id'
        """
        self.name = name
        self.description = description
        self.schema_name = schema_name
        self.table_name = table_name or name.lower().replace(' ', '_')
        self.pk_column_name = pk_column_name or f'{self.table_name}_id'
        self.attributes = []
        self.entity_links = []
        self.data_set = None  # the data set that contains the entity

    def __repr__(self) -> str:
        return f'<Entity "{self.name}">'

    def add_attribute(self, name: str, description: str, column_name: str = None, type: 'Type' = None,
                      high_cardinality: bool = False, personal_data: bool = False, important_field: bool = False,
                      accessible_via_entity_link: bool = True) -> None:
        """
        Adds a property based on a column in the underlying dimensional table to the entity
        Args:
            name: How the attribute is displayed in frontends, e.g. "Order date"
            description: A meaningful business definition of the attribute. E.g. "The date when the order was placed"
            column_name: The name of the column in the underlying database table.
                Defaults to the lower-cased name with white-spaced replaced by underscores.
            type: The type of the attribute, e.g. Type.ID, Type.Date, Type.DURATION. Defaults to None.
                Type.ID: Attribute is converted to text in flattened table.
                Type.DATE: Attribute uses the public dimension "Date" in Mondrian.
                Type.DURATION: Attribute uses the public dimension "Duration" in Mondrian.
            high_cardinality: It refers to columns with values that are very uncommon or unique. Defaults to False.
            personal_data: It refers to person related data, e.g. "Email address", "Name".
            important_field: It refers to key business attribute.
            accessible_via_entity_link: If an attribute could be linked from other entities via EntityLink. Defaults to
                True. If False, e.g. attribute "Booking sequence" in booking_entity, the attribute is private to
                booking_entity in booking data_set and can't be accessed via EntityLink as "Last booking sequence".
        """
        self.attributes.append(
            Entity.Attribute(
                name=name,
                description=description,
                column_name=column_name or name.lower().replace(' ', '_'),
                accessible_via_entity_link=accessible_via_entity_link,
                type=type,
                high_cardinality=high_cardinality,
                personal_data=personal_data,
                important_field=important_field
            ))

    def link_entity(self, target_entity: 'Entity', fk_column: str = None, prefix: str = '') -> None:
        """
        Adds a link from the entity to another entity, corresponds to a foreign key relationship
        Args:
            target_entity: The referenced entity, e.g. an "Order" entity
            fk_column: The foreign key column in the source entity, e.g. "first_order_fk" in the "customer" table
            prefix: Attributes from the linked entity will be prefixed with this, e.g "First order". Defaults to empty
            string.
        """
        self.entity_links.append(
            Entity.EntityLink(
                target_entity=target_entity,
                fk_column=fk_column or f'{target_entity.table_name}_fk',
                prefix=prefix))

    def find_entity_link(self, target_entity_name: str, prefix: str = None) -> 'Entity.EntityLink':
        """Find an EntityLink by it's target entity name or prefix."""

        entity_links = [entity_link for entity_link in self.entity_links
                        if entity_link.target_entity.name == target_entity_name
                        and (prefix is None or prefix == entity_link.prefix)]

        prefix_message = f'prefix "{prefix}"' if prefix else "no prefix"
        if not entity_links:
            raise LookupError(f"""Linked entity "{target_entity_name}" / {prefix_message} not found in {self}""")

        if len(entity_links) > 1:
            raise LookupError(f"""Multiple linked entities found for "{target_entity_name}" / {prefix_message}""")

        return entity_links[0]

    def find_attribute(self, attribute_name: str):
        """Find an attribute by it's name"""
        attribute = next((attribute for attribute in self.attributes if attribute.name == attribute_name), None)
        if not attribute:
            raise KeyError(f'Attribute "{attribute_name}" not found in f{self}')
        return attribute

    class Attribute():
        """A property of an entity, corresponds to a column in the underlying dimensional table"""

        def __init__(self, name: str, description: str, column_name: str,
                     accessible_via_entity_link: bool, type: 'Type' = None, high_cardinality: bool = False,
                     personal_data: bool = False, important_field: bool = False) -> None:
            self.name = name
            self.description = description
            self.column_name = column_name
            self.type = type
            self.high_cardinality = high_cardinality
            self.personal_data = personal_data
            self.important_field = important_field
            self.accessible_via_entity_link = accessible_via_entity_link

        def __repr__(self) -> str:
            return f'<Attribute "{self.name}">'

    class EntityLink():
        """A link from an entity to another entity, corresponds to a foreign key relationship"""

        def __init__(self, target_entity: 'Entity', fk_column: str = None, prefix: str = '') -> None:
            self.target_entity = target_entity
            self.fk_column = fk_column or f'{target_entity.table_name}_fk'
            self.prefix = prefix

        def __repr__(self) -> str:
            prefix_repr = f' / "{self.prefix}"' if self.prefix else ''
            return f'<EntityLink "{self.target_entity.name}"{prefix_repr}>'


class Aggregation(enum.EnumMeta):
    """
    The aggregation method to use.
    """
    SUM = 'sum'
    AVERAGE = 'avg'
    COUNT = 'count'
    DISTINCT_COUNT = 'distinct-count'


class NumberFormat(enum.EnumMeta):
    """
    The way to format number in Mondrian.
    """
    STANDARD = 'Standard'
    CURRENCY = 'Currency'
    PERCENT = 'Percent'


class Type(enum.EnumMeta):
    """
    Specification for attribute's type:
        Type.ID: Attribute is converted to text in flattened table.
        Type.DATE: Attribute can be created as Mondrian Dimension with template if template is specified in
            `mondrian_dimension_templates` in config.py.
        Type.DURATION: Attribute can be created as Mondrian Dimension with template if template is specified in
            `mondrian_dimension_templates` in config.py.
        Type.ENUM: Attributes is converted to text in flattened table.
        Type.ARRAY: Attribute is excluded as dimension in Mondrian schema.
    """
    DATE = 'date'
    DURATION = 'duration'
    ID = 'id'
    ENUM = 'enum'
    ARRAY = 'array'


class Metric(abc.ABC):
    def __init__(self, name: str, description: str, important_field: bool = False) -> None:
        """
        A numeric aggregation on columns of an entity table
        Args:
            name: How the metric is displayed in front-ends, e.g. "Revenue after cancellations"
            description: A meaningful business definition of the metric
            important_field: It refers to key business metrics.
        """
        self.name = name
        self.description = description
        self.important_field = important_field
        self.data_set = None  # the data set that contains the metric

    @abc.abstractmethod
    def display_formula(self):
        """Returns a documentation string for displaying the formula in the frontend"""
        pass

    def sql_formula(self):
        """A SQL expression that can compute the measure from a row of the fact table"""
        pass


class SimpleMetric(Metric):
    def __init__(self, name: str, description: str, column_name: str, aggregation: Aggregation,
                 important_field: bool = False,
                 number_format: NumberFormat = NumberFormat.STANDARD):
        """
        A metric that is computed as a direct aggregation on a entity table column
        Args:
            name: How the metric is displayed in front-ends, e.g. "Revenue after cancellations"
            description: A meaningful business definition of the metric
            column_name: The column that the aggregation is based on
            aggregation: The aggregation method to use
            important_field: It refers to key business metrics.
            number_format: The way to format string in Mondrian. Default to NumberFormat.STANDARD.
        """
        super().__init__(name, description)
        self.column_name = column_name
        self.aggregation = aggregation
        self.important_field = important_field
        self.number_format = number_format
        self.data_set = None

    def __repr__(self) -> str:
        return f'<Metric "{self.name}": {self.display_formula()})>'

    def display_formula(self) -> str:
        return f"{self.aggregation}({self.column_name})"

    def sql_formula(self):
        if self.aggregation in [Aggregation.DISTINCT_COUNT, Aggregation.COUNT]:
            return f'("{self.data_set.entity.name}".{self.column_name} IS NOT NULL) ::INTEGER :: SMALLINT'
        else:
            return f'COALESCE("{self.data_set.entity.name}".{self.column_name}, 0)'


class ComposedMetric(Metric):
    def __init__(self, name: str, description: str,
                 parent_metrics: [Metric], formula_template: str, important_field: bool = False,
                 number_format: NumberFormat = NumberFormat.STANDARD) -> None:
        """
        A metric that is based on a list of simple metrics.
        Args:
            name: How the metric is displayed in front-ends, e.g. "Revenue after cancellations"
            description: A meaningful business definition of the metric
            parent_metrics: The parent metrics that this metric is composed of
            formula_template: How to compose the parent metrics, with '{}' as placeholders
                Examples: '{} + {}', '{} / ({} + {})'
            important_field: It refers to key business metrics.
            number_format: The way to format string in Mondrian. Default to NumberFormat.STANDARD.
        """
        super().__init__(name, description)
        self.parent_metrics = parent_metrics
        self.formula_template = formula_template
        self.important_field = important_field
        self.number_format = number_format
        self.data_set = None

    def __repr__(self) -> str:
        return f'<ComposedMetric "{self.name}": {self.display_formula()}>'

    def display_formula(self) -> str:
        return self.formula_template.format(*[f'[{metric.name}]' for metric in self.parent_metrics])

    def sql_formula(self):
        if '/' in self.formula_template:
            return self.formula_template.format(
                *[f'(NULLIF({metric.sql_formula()}, 0.0))' for metric in self.parent_metrics])
        else:
            return self.formula_template.format(*[f'({metric.sql_formula()})' for metric in self.parent_metrics])


class DataSet():
    def __init__(self, entity: Entity, name: str, max_entity_link_depth: int = None):
        """
        An entity with its metrics and recursively linked entities.
        Args:
            entity: The underlying entity with its attributes and linked other entities
            name: The name of the data set.
            max_entity_link_depth: The maximal number of entity link instances to a connected entity from the entity of
                data set. Example: With max_entity_link_depth = 2, each of the connected entity could be reached from
                the data set's entity within 2 entity link instances.
        """
        self.entity = entity
        self.entity.data_set = self
        self.name = name
        self.metrics = {}
        self.excluded_paths = set()
        self.included_paths = set()
        self.included_attributes = {}
        self.excluded_attributes = {}
        self.max_entity_link_depth = max_entity_link_depth

    def __repr__(self) -> str:
        return f'<DataSet "{self.entity.name}">'

    def add_simple_metric(self, name: str, description: str, column_name: str, aggregation: Aggregation,
                          important_field: bool = False,
                          number_format: NumberFormat = NumberFormat.STANDARD):
        """
        Add a metric that is computed as a direct aggregation on a entity table column
        Args:
            name: How the metric is displayed in front-ends, e.g. "Revenue after cancellations"
            description: A meaningful business definition of the metric
            column_name: The column that the aggregation is based on
            aggregation: The aggregation method to use
            important_field: It refers to key business metrics.
            number_format: The way to format string in Mondrian. Default to NumberFormat.STANDARD.
        """
        if name in self.metrics:
            raise ValueError(f'Metric "{name}" already exists in data set "{self.name}"')

        self.metrics[name] = SimpleMetric(
            name=name,
            description=description,
            column_name=column_name,
            aggregation=aggregation,
            important_field=important_field,
            number_format=number_format)

        self.metrics[name].data_set = self

    def add_composed_metric(self, name: str, description: str, formula: str, important_field: bool = False,
                            number_format: NumberFormat = NumberFormat.STANDARD):
        """
        Add a metric that is based on a list of simple metrics.
        Args:
            name: How the metric is displayed in front-ends, e.g. "Revenue after cancellations"
            description: A meaningful business definition of the metric
            formula: How to compute the metric. Examples: [Metric A] + [Metric B],  [Metric A] / ([Metric B] + [Metric C])
            important_field: It refers to key business metrics.
            number_format: The way to format string in Mondrian. Default to NumberFormat.STANDARD.
        """
        if name in self.metrics:
            raise ValueError(f'Metric "{name}" already exists in data set "{self.name}"')

        # ' [a] \n + [b]' -> '[a] + [b]'
        formula_cleaned = re.sub("\s\s+", " ", formula.strip().replace('\n', ''))

        # split '[a] + [b]' -> ['', 'a', ' + ', 'b', '']
        formula_split = re.split(r'\[(.*?)\]', formula_cleaned)

        parent_metrics = []
        for metric_name in formula_split[1::2]:  # 1::2  start at second, take every 2nd,
            if metric_name not in self.metrics:
                raise ValueError(f'Could not find metric "{metric_name} in data set "{self.name}"')
            parent_metrics.append(self.metrics[metric_name])

        self.metrics[name] = ComposedMetric(name=name,
                                            description=description,
                                            parent_metrics=parent_metrics,
                                            formula_template='{}'.join(formula_split[0::2]),
                                            important_field=important_field,
                                            number_format=number_format)

        self.metrics[name].data_set = self

    _PathSpec = typing.TypeVar('_PathSpec', typing.Sequence[typing.Union[str, typing.Tuple[str, str]]], bytes)

    def _parse_path(self, entity: Entity, path: _PathSpec) -> typing.Union[
        typing.Tuple, typing.Tuple[Entity.EntityLink, Entity.EntityLink]]:
        """
        Helper function for parsing path specifications into a tuple of entity link instances

        Args:
            entity: the entity for which to resolve the entity links
            path: How to get to the entity from the entity of the data set.
                  A list of either strings (target entity names) or tuples of strings (target entity name + prefix).
                  Example: ['Entity 1', ('Entity 2', 'Prefix'), 'Entity 3']
        """
        if not path:
            return ()

        if not (isinstance(path[0], str) or (isinstance(path[0], tuple) and len(path[0]) == 2)):
            raise TypeError(f'Expecting a string or a tuple of two strings, got: {path[0]}')

        target_entity_name, prefix = (path[0], None) if isinstance(path[0], str) else path[0]
        entity_link = entity.find_entity_link(target_entity_name, prefix)

        return (entity_link,) + self._parse_path(entity_link.target_entity, path[1::])

    def exclude_path(self, path: _PathSpec):
        """
        Exclude a connected entity from generated data set tables by specifying the entity links to that entity

        Args:
            path: How to get to the entity from the data set entity.
                  A list of either strings (target entity names) or tuples of strings (target entity name + prefix).
                  Example: ['Entity 1', ('Entity 2', 'Prefix'), 'Entity 3']
        """
        self.excluded_paths.add(self._parse_path(self.entity, path))

    def include_path(self, path: _PathSpec):
        """
        Include a connected entity in generated data set tables that would otherwise be automatically excluded
        by the max_entity_link_depth setting.

        Args:
            path: How to get to the entity from the data set entity.
                  A list of either strings (target entity names) or tuples of strings (target entity name + prefix).
                  Example: ['Entity 1', ('Entity 2', 'Prefix'), 'Entity 3']
        """
        self.included_paths.add(self._parse_path(self.entity, path))

    def exclude_attributes(self, path: _PathSpec, attribute_names: [str] = None):
        """
        Exclude attributes of a connected entity in generated data set tables.

        Args:
            path: How to get to the entity from the data set entity.
                  A list of either strings (target entity names) or tuples of strings (target entity name + prefix).
                  Example: ['Entity 1', ('Entity 2', 'Prefix'), 'Entity 3']
            attribute_names: A list of name of attributes to be excluded. If not provided, then exclude all attributes
        """
        entity_links = self._parse_path(self.entity, path)
        entity = entity_links[-1].target_entity

        if not attribute_names:
            self.excluded_attributes[entity_links] = entity.attributes
        else:
            self.excluded_attributes[entity_links] = [entity.find_attribute(attribute_name) for attribute_name in
                                                      attribute_names]

    def include_attributes(self, path: _PathSpec, attribute_names: [str]):
        """
        Exclude all attributes except the specified ones of a connected entity in generated data set tables.

        Args:
            path: How to get to the entity from the data set entity.
                  A list of either strings (target entity names) or tuples of strings (target entity name + prefix).
                  Example: ['Entity 1', ('Entity 2', 'Prefix'), 'Entity 3']
            attribute_names: A list of name of attributes to be included.
        """
        entity_links = self._parse_path(self.entity, path)

        self.included_attributes[entity_links] = [entity_links[-1].target_entity.find_attribute(attribute_name) for
                                                  attribute_name in attribute_names]

    def connected_attributes(self, include_personal_data: bool = True) -> {(Entity.EntityLink): [Entity.Attribute]}:
        result = {(): self.entity.attributes}

        for path in paths_to_connected_entities(self):
            attributes = []
            entity = path[-1].target_entity
            for attribute in entity.attributes:
                if ((path in self.included_attributes and attribute in self.included_attributes[path])
                    or (path not in self.included_attributes)) \
                        and ((path in self.excluded_attributes and attribute not in self.excluded_attributes[path])
                             or (path not in self.excluded_attributes)) \
                        and attribute.accessible_via_entity_link and (
                        include_personal_data or not attribute.personal_data):
                    attributes.append(attribute)
                    result[path] = attributes
        return result


def connected_entities(entity: Entity) -> [Entity]:
    """ Find all recursively linked entities. """
    result = set([entity])

    def traverse_graph(entity: Entity):
        for link in entity.entity_links:
            if link.target_entity not in result:
                result.add(link.target_entity)
                traverse_graph(link.target_entity)

    traverse_graph(entity)

    return result


def paths_to_connected_entities(data_set: DataSet) -> typing.List[typing.Tuple[Entity.EntityLink]]:
    """
    Get all possible paths to connected entities (tuples of entity links) that are not explicitly excluded

    Args:
        data_set: An DataSet object.
    Returns:
        A list of tuple of entity link instances.
    """

    paths = []

    def _append_path_including_subpaths(paths, path) -> typing.List[typing.Tuple[Entity.EntityLink]]:
        """Append a path and its subpaths to the list of paths, if they do not already exist. A subpath always starts
        at the beginning of the path: (1,2,3) -> (1,), (1,2), (1,2,3)
        """
        for i in range(len(path)):
            if path[:i+1] not in paths:
                paths.append(path[:i+1])
        return paths

    def traverse_graph(entity: Entity, current_path: tuple):
        for entity_link in entity.entity_links:
            path = current_path + (entity_link,)

            if (entity_link not in current_path  # check for circles in paths
                    and (path not in data_set.excluded_paths)  # explicitly excluded paths
                    and not (data_set.max_entity_link_depth is not None  # limit by depth or excplictly include
                             and len(path) > data_set.max_entity_link_depth
                             and path not in data_set.included_paths)):
                _append_path_including_subpaths(paths, path)
                traverse_graph(entity_link.target_entity, path)

    traverse_graph(data_set.entity, ())

    return paths


def generate_attribute_name(attribute: Entity.Attribute, path: typing.Tuple['Entity.EntityLink'] = None) -> str:
    """Generate a meaningful business name by concatenating the prefix of entity link instances and original
    name of attribute. """

    def first_lower(string: str = ''):
        """Lowercase first letter if the first two letter are not capitalized """
        if not re.match(r'([A-Z]){2}', string):
            return string[:1].lower() + string[1:]
        else:
            return string

    if path:
        prefix = ' '.join([entity_link.prefix.lower() for entity_link in path])
        return normalize_name(prefix + ' ' + first_lower(attribute.name))
    else:
        return normalize_name(attribute.name)


def normalize_name(attribute_name_or_table_alias) -> str:
    """Helper function to normalize attribute's name or table alias."""
    import hashlib

    def init_cap(string: str) -> str:
        return string[0].upper() + string[1::]

    def remove_repeating_words(string: str) -> str:
        """Remove repeating words from the generated name, e.g. "First booking booking ID" -> "First booking ID" """
        return re.sub(r'\b(\w+)( \1\b)+', r'\1', string)

    def limit_column_length(string: str) -> str:
        """Returns a unique column name within 63 bytes. """
        if len(string) > 63:
            m = hashlib.md5()
            m.update(string.encode('utf-8'))
            return string[:55] + m.hexdigest()[:8]
        else:
            return string

    return limit_column_length(
        init_cap(re.sub('\s\s+', ' ', remove_repeating_words(attribute_name_or_table_alias).lstrip())))
