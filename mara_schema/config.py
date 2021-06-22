import functools
from .data_set import DataSet
from .entity import Entity

@functools.lru_cache(maxsize=None)
def data_sets() -> [DataSet]:
    """Returns all available data_sets."""
    from .example import example_data_sets
    return example_data_sets()

@functools.lru_cache(maxsize=None)
def entities() -> [Entity]:
    """Returns all available entities."""
    from .example import example_entities
    return example_entities()
