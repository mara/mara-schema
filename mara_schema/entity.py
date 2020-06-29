from .attribute import Attribute, Type


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

    def add_attribute(self, name: str, description: str, column_name: str = None, type: Type = None,
                      high_cardinality: bool = False, personal_data: bool = False, important_field: bool = False,
                      accessible_via_entity_link: bool = True) -> None:
        """
        Adds a property based on a column in the underlying dimensional table to the entity

        Args:
            name: How the attribute is displayed in front-ends, e.g. "Order date"
            description: A meaningful business definition of the attribute. E.g. "The date when the order was placed"
            column_name: The name of the column in the underlying database table.
                Defaults to the lower-cased name with white-spaced replaced by underscores.
            type: The type of the attribute, see definition of `Type` enum
            high_cardinality: It refers to columns with values that are very uncommon or unique. Defaults to False.
            personal_data: It refers to person related data, e.g. "Email address", "Name".
            important_field: A field that highlights the the data set. Shown by default in overviews
            accessible_via_entity_link: If False, then this attribute is excluded from data sets that are not
                     based on this entity
        """
        self.attributes.append(
            Attribute(
                name=name,
                description=description,
                column_name=column_name or name.lower().replace(' ', '_'),
                accessible_via_entity_link=accessible_via_entity_link,
                type=type,
                high_cardinality=high_cardinality,
                personal_data=personal_data,
                important_field=important_field
            ))

    def link_entity(self, target_entity: 'Entity', fk_column: str = None,
                    prefix: str = None, description=None) -> None:
        """
        Adds a link from the entity to another entity, corresponds to a foreign key relationship

        Args:
            target_entity: The referenced entity, e.g. an "Order" entity
            fk_column: The foreign key column in the source entity, e.g. "first_order_fk" in the "customer" table
            prefix: Attributes from the linked entity will be prefixed with this, e.g "First order".
                    Defaults to the name of the linked entity.
            description: A short explanation for the relation between the entity and target entity
        """
        self.entity_links.append(
            EntityLink(
                target_entity=target_entity,
                fk_column=fk_column or f'{target_entity.table_name}_fk',
                prefix=prefix if prefix is not None else target_entity.name,
                description=description))

    def find_entity_link(self, target_entity_name: str, prefix: str = None) -> 'EntityLink':
        """Find an EntityLink by its target entity name or prefix."""

        entity_links = [entity_link for entity_link in self.entity_links
                        if entity_link.target_entity.name == target_entity_name
                        and (prefix is None or prefix == entity_link.prefix)]

        if not entity_links:
            raise LookupError(f"""Linked entity "{target_entity_name}" / "{prefix or ''}" not found in {self}""")

        if len(entity_links) > 1:
            raise LookupError(f"""Multiple linked entities found for "{target_entity_name}" / "{prefix}" """)

        return entity_links[0]

    def find_attribute(self, attribute_name: str) -> Attribute:
        """Find an attribute by its name"""
        attribute = next((attribute for attribute in self.attributes if attribute.name == attribute_name), None)
        if not attribute:
            raise KeyError(f'Attribute "{attribute_name}" not found in f{self}')
        return attribute

    def connected_entities(self) -> ['Entity']:
        """ Find all recursively linked entities. """
        result = set([self])

        def traverse_graph(entity: Entity):
            for link in entity.entity_links:
                if link.target_entity not in result:
                    result.add(link.target_entity)
                    traverse_graph(link.target_entity)

        traverse_graph(self)

        return result


class EntityLink():
    def __init__(self, target_entity: Entity, prefix: str,
                 description: str= None, fk_column: str = None) -> None:
        """
        A link from an entity to another entity, corresponds to a foreign key relationship

        Args:
            target_entity: The referenced entity, e.g. an "Order" entity
            prefix: Attributes from the linked entity will be prefixed with this, e.g "First order".
            description: A short explanation for the relation between the entity and target entity
            fk_column: The foreign key column in the source entity, e.g. "first_order_fk" in the "customer" table
        """
        self.target_entity = target_entity
        self.prefix = prefix
        self.description = description
        self.fk_column = fk_column or f'{target_entity.table_name}_fk'

    def __repr__(self) -> str:
        return f'<EntityLink "{self.target_entity.name}" / "{self.prefix}">'
