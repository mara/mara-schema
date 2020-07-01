import enum
import re

import typing


class Type(enum.EnumMeta):
    """
    Attribute types that need special treatment in artifact creation
        Type.ID: A numeric ID that is converted to text in a flattened table so that it can be filtered
        Type.DATE: Date attribute as a foreign_key to a date dimension
        Type.DURATION: Duration attribute as a foreign_key to a duration dimension
        Type.ENUM: Attributes that is converted to text in a flattened table.
        Type.ARRAY: Attribute of type array
    """
    DATE = 'date'
    DURATION = 'duration'
    ID = 'id'
    ENUM = 'enum'
    ARRAY = 'array'


class Attribute():
    """A property of an entity, corresponds to a column in the underlying dimensional table"""

    def __init__(self, name: str, description: str, column_name: str,
                 accessible_via_entity_link: bool, type: 'Type' = None, high_cardinality: bool = False,
                 personal_data: bool = False, important_field: bool = False) -> None:
        """See documentation of function Entity.add_attribute"""
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

    def prefixed_name(self, path: typing.Tuple['EntityLink'] = None) -> str:
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
            return normalize_name(prefix + ' ' + first_lower(self.name))
        else:
            return normalize_name(self.name)


def normalize_name(name: str, max_length: int = 63) -> str:
    """
    Makes "Foo bar baz" out of "foo bar bar baz"
    Args:
        name: the name to normalize
        max_length: optionally limit length by replacing too long part with a hash of the name
    """

    def first_letter_capitalize(string: str) -> str:
        return string[0].upper() + string[1::]

    # Remove repeating words from the generated name, e.g. "First booking booking ID" -> "First booking ID"
    name = re.sub(r'\b(\w+)( \1\b)+', r'\1', name).strip()

    # Remove duplicate whitespace
    name = re.sub('\s\s+', ' ', name)

    name = first_letter_capitalize(name)

    # Limit length

    if max_length and len(name) > max_length:
        import hashlib
        m = hashlib.md5()
        m.update(name.encode('utf-8'))
        return name[:(max_length - 8)] + m.hexdigest()[:8]

    return name
