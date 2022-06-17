API
===

.. module:: mara_schema

This part of the documentation covers all the interfaces of Mara Schema. For
parts where the package depends on external libraries, we document the most
important right here and provide links to the canonical documentation.


Entities
--------

.. module:: mara_schema.entity

.. autoclass:: Entity
    :members:
    :special-members: __init__

.. autoclass:: EntityLink
    :special-members: __init__


Attributes
----------

.. module:: mara_schema.attribute

.. autoclass:: Attribute
    :members:
    :special-members: __init__

.. autoclass:: Type

.. autofunction:: normalize_name


Data sets
---------

.. module:: mara_schema.data_set

.. autoclass:: DataSet
    :members:
    :special-members: __init__


Metrics
-------

.. module:: mara_schema.metric

.. autoclass:: Aggregation

.. autoclass:: NumberFormat

.. autoclass:: SimpleMetric
    :members:
    :special-members: __init__

.. autoclass:: ComposedMetric
    :members:
    :special-members: __init__


SQL Generation
--------------

.. module:: mara_schema.sql_generation

.. autofunction:: data_set_sql_query
