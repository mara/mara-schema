import re
import typing

from .attribute import Attribute
from .entity import Entity, EntityLink
from .metric import NumberFormat, Aggregation, SimpleMetric, ComposedMetric


class DataSet():
    def __init__(self, entity: Entity, name: str):
        """
        An entity with its metrics and recursively linked entities.

        Args:
            entity: The underlying entity with its attributes and linked other entities
            name: The name of the data set.
        """
        self.entity = entity
        self.name = name

        self.entity.data_set = self
        self.metrics = {}
        self.excluded_paths = set()
        self.included_attributes = {}
        self.excluded_attributes = {}

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
            number_format: The way to format a string. Defaults to NumberFormat.STANDARD.
        """
        if name in self.metrics:
            raise ValueError(f'Metric "{name}" already exists in data set "{self.name}"')

        self.metrics[name] = SimpleMetric(
            name=name,
            description=description,
            data_set=self,
            column_name=column_name,
            aggregation=aggregation,
            important_field=important_field,
            number_format=number_format)

    def add_composed_metric(self, name: str, description: str, formula: str, important_field: bool = False,
                            number_format: NumberFormat = NumberFormat.STANDARD):
        """
        Add a metric that is based on a list of simple metrics.

        Args:
            name: How the metric is displayed in front-ends, e.g. "Revenue after cancellations"
            description: A meaningful business definition of the metric
            formula: How to compute the metric. Examples: [Metric A] + [Metric B],  [Metric A] / ([Metric B] + [Metric C])
            important_field: It refers to key business metrics.
            number_format: The way to format a string. Defaults to NumberFormat.STANDARD.
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
                                            data_set=self,
                                            parent_metrics=parent_metrics,
                                            formula_template='{}'.join(formula_split[0::2]),
                                            important_field=important_field,
                                            number_format=number_format)

    _PathSpec = typing.TypeVar('_PathSpec', typing.Sequence[typing.Union[str, typing.Tuple[str, str]]], bytes)

    def _parse_path(self, entity: Entity, path: _PathSpec) -> typing.Union[
        typing.Tuple, typing.Tuple[EntityLink, EntityLink]]:
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
        Include all attributes except the specified ones of a connected entity in generated data set tables.

        Args:
            path: How to get to the entity from the data set entity.
                  A list of either strings (target entity names) or tuples of strings (target entity name + prefix).
                  Example: ['Entity 1', ('Entity 2', 'Prefix'), 'Entity 3']
            attribute_names: A list of name of attributes to be included.
        """
        entity_links = self._parse_path(self.entity, path)

        self.included_attributes[entity_links] = [entity_links[-1].target_entity.find_attribute(attribute_name) for
                                                  attribute_name in attribute_names]

    def paths_to_connected_entities(self) -> [(EntityLink,)]:
        """
        Get all possible paths to connected entities (tuples of entity links)
        - that are not explicitly excluded
        - that are are not beyond the max link depth or that are explicitly included
        """

        paths = []

        def _append_path_including_subpaths(paths, path) -> typing.List[typing.Tuple[EntityLink]]:
            """Append a path and its subpaths to the list of paths, if they do not already exist. A subpath always starts
            at the beginning of the path: (1,2,3) -> (1,), (1,2), (1,2,3)
            """
            for i in range(len(path)):
                if path[:i + 1] not in paths:
                    paths.append(path[:i + 1])
            return paths

        def traverse_graph(entity: Entity, current_path: tuple):
            for entity_link in entity.entity_links:
                path = current_path + (entity_link,)

                if (entity_link not in current_path  # check for circles in path
                        and (path not in self.excluded_paths)  # explicitly excluded paths
                ):
                    _append_path_including_subpaths(paths, path)
                    traverse_graph(entity_link.target_entity, path)

        traverse_graph(self.entity, ())

        return paths

    def connected_attributes(self, include_personal_data: bool = True) -> {(EntityLink,): {str: Attribute}}:
        """
        Returns all attributes with their prefixed name from all connected entities.

        Args:
            include_personal_data: If False, then exclude fields that are marked as personal data

        Returns:
            A dictionary with the paths as keys and dictionaries of prefixed attribute names and
            attributes as values. Example:
                {(<EntityLink 1>, <EntityLink 2): {'Prefixed attribute 1 name': <Attribute 1>,
                                                   'Prefixed attribute 2 name': <Attribute 2>},
                 ..}
        """
        result = {(): {attribute.prefixed_name(): attribute for attribute in self.entity.attributes}}

        for path in self.paths_to_connected_entities():
            result[path] = {}
            entity = path[-1].target_entity
            for attribute in entity.attributes:
                if ((path in self.included_attributes and attribute in self.included_attributes[path])
                    or (path not in self.included_attributes)) \
                        and ((path in self.excluded_attributes and attribute not in self.excluded_attributes[path])
                             or (path not in self.excluded_attributes)) \
                        and attribute.accessible_via_entity_link and (
                        include_personal_data or not attribute.personal_data):
                    result[path][attribute.prefixed_name(path)] = attribute
        return result

    def id(self):
        """Returns a representation that can be used in urls"""
        from html import escape
        return escape(self.name.replace(' ', '_').lower())
