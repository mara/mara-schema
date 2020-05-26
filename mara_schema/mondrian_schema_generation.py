import enum
from io import BytesIO

from lxml import etree
from mara_schema import config
from mara_schema.schema import DataSet, SimpleMetric, ComposedMetric, Aggregation, NumberFormat, Type, \
    generate_attribute_name
from mara_schema.sql_generation import generate_fk_from_attribute, generate_mondrian_fact_table_fk


class Hierarchy():
    def __init__(self, name, primary_key: str = None):
        """
        This class defines a Mondrian ElementHierarchy.
        For more information see https://mondrian.pentaho.com/documentation/xml_schema.php#ElementHierarchy.
        Args:
            name: The attribute "name" for Mondrian's ElementHierarchy.
            primary_key: The attribute "primaryKey" for Mondrian's ElementLevel.
        """
        self.name = name
        self.primary_key = primary_key
        self.levels = []
        self.table = tuple()

    def __repr__(self):
        return f'<Hierarchy "{self.name}">'

    def add_level(self, name, column, name_column=None, level_type='Regular', unique_members=False,
                  type='String'):
        """
        Add a Mondrian ElementLevel.
        For more information see https://mondrian.pentaho.com/documentation/xml_schema.php#ElementLevel
        Args:
            name: The attribute "name" for Mondrian's ElementLevel.
            column: The attribute "column" for Mondrian's ElementLevel.
            name_column: The attribute "nameColumn" for Mondrian's ElementLevel.
            level_type: The attribute "levelType" for Mondrian's ElementLevel.
            unique_members: The attribute "uniqueMembers" for Mondrian's ElementLevel.
            type: The attribute "type" for Mondrian's ElementLevel.

        Returns:

        """
        self.levels.append(
            Hierarchy.Level(name=name, column=column, name_column=name_column, type=type, level_type=level_type,
                            unique_members=unique_members))

    def add_table(self, schema_name, name):
        """
        Add a Mondrian ElementTable.
        For more information see https://mondrian.pentaho.com/documentation/xml_schema.php#ElementTable
        Args:
            schema_name: The attribute "schema" for Mondrian's ElementTable.
            name: The attribute "name" for Mondrian's ElementTable.

        Returns:

        """
        self.table = (schema_name, name)

    class Level():
        def __init__(self, name: str = None, column: str = None, name_column: str = None, type: str = 'String',
                     level_type: str = 'Regular', unique_members: bool = False):
            """
            This class defines a Mondrian ElementLevel.
            For more information see https://mondrian.pentaho.com/documentation/xml_schema.php#ElementLevel
            Args:
                name: The attribute "name" for Mondrian's ElementLevel.
                column: The attribute "column" for Mondrian's ElementLevel.
                name_column: The attribute "nameColumn" for Mondrian's ElementLevel.
                level_type: The attribute "levelType" for Mondrian's ElementLevel.
                unique_members: The attribute "uniqueMembers" for Mondrian's ElementLevel.
                type: The attribute "type" for Mondrian's ElementLevel.
            """
            self.name = name
            self.column = column
            self.name_column = name_column
            self.type = type
            self.level_type = level_type
            self.unique_members = unique_members


class Dimension():
    def __init__(self, name, description):
        """
        A Dimension is a collection of hierarchies.
        Args:
            name: Name of this dimension.
            description: Description of this dimension.
        """
        self.name = name
        self.description = description
        self.hierarchies = []


class PrivateDimension(Dimension):
    def __init__(self, name, description, column_name):
        """
        A private dimension belongs to a Cube.
        Args:
            name: Name of this dimension.
            description: Description of this dimension.
            column_name: The name of the column.
        """
        super().__init__(name=name, description=description)
        self.column_name = column_name
        self.hierarchies = []

    def add_hierarchy(self):
        """
        Add a Mondrian ElementHierarchy to a Dimension.
        For more information see https://mondrian.pentaho.com/documentation/xml_schema.php#ElementHierarchy.
        """
        hierarchy = Hierarchy(name=self.name)
        hierarchy.add_level(name=self.name, column=self.column_name)
        self.hierarchies.append(hierarchy)

    def get_xml_element(self):
        """
        Returns an XML representation of this object.
        """
        dim = etree.Element("Dimension", name=self.name, description=self.description)
        for item in self.hierarchies:
            hierarchy = etree.SubElement(dim, "Hierarchy", allMemberName='All ' + item.name, hasAll="true")
            for level in item.levels:
                etree.SubElement(hierarchy, "Level", name=level.name, column=level.column, uniqueMembers="true")
        return dim


class LinkedDimension(Dimension):
    def __init__(self, name, description, column_name, foreign_key, primary_key, schema_name, table_name):
        """
        Linked dimension is a private dimension, which is joined to the cube with a foreign_key column in the fact table
            and a primary_key column from another dimension table.
        Args:
            name: Name of this dimension.
            description: Description of this dimension.
            column_name: The name of the column.
            foreign_key: The name of the column in the fact table which joins to the leaf level of this dimension.
            primary_key: The primary_key column from another dimension table.
            schema_name: The attribute "schema" for Mondrian's ElementTable.
            table_name: The attribute "name" for Mondrian's ElementTable.
        """
        super().__init__(name=name, description=description)
        self.hierarchies = []
        self.column_name = column_name
        self.foreign_key = foreign_key
        self.primary_key = primary_key
        self.schema_name = schema_name
        self.table_name = table_name
        self.add_hierarchy()

    def add_hierarchy(self):
        """
        Add a Mondrian ElementHierarchy to a Dimension.
        For more information see https://mondrian.pentaho.com/documentation/xml_schema.php#ElementHierarchy.
        """
        hierarchy = Hierarchy(name=self.name, primary_key=self.primary_key)
        hierarchy.add_table(schema_name=self.schema_name, name=self.table_name)
        hierarchy.add_level(name=self.name, column=self.column_name)
        self.hierarchies.append(hierarchy)

    def get_xml_element(self):
        """
        Returns an XML representation of this object.
        """
        dim = etree.Element("Dimension", name=self.name, description=self.description,
                            foreignKey=self.foreign_key)
        for item in self.hierarchies:
            hierarchy = etree.SubElement(dim, "Hierarchy", allMemberName='All ' + item.name, hasAll="true",
                                         primaryKey=item.primary_key)

            etree.SubElement(hierarchy, "Table", name=item.table[1],
                             schema=item.table[0])
            for level in item.levels:
                etree.SubElement(hierarchy, "Level", name=level.name,
                                 column=level.column, uniqueMembers="true")

        return dim


class TemplatedDimension(Dimension):
    def __init__(self, name, description, foreign_key, template: Type):
        """
        A DimensionUsage is usage of a shared Dimension within the context of a cube.
        For more information see https://mondrian.pentaho.com/documentation/xml_schema.php#DimensionUsage
        Args:
            name: Name of this dimension.
            description: Description of this dimension.
            source: The attribute "source" for Mondrian's ElementLevel.
            foreign_key: The name of the column in the fact table which joins to the leaf level of this dimension.
        """
        super().__init__(name=name, description=description)
        self.foreign_key = foreign_key
        self.template = template

    def add_hierarchy(self, hierarchy: Hierarchy):
        """
        Add a Mondrian ElementHierarchy to a Dimension.
        For more information see https://mondrian.pentaho.com/documentation/xml_schema.php#ElementHierarchy.
        """
        self.hierarchies.append(hierarchy)

    def get_xml_element(self):
        """
        Returns an XML representation of this object.
        """
        if self.template == Type.DATE:
            type = 'TimeDimension'
        else:
            type = 'StandardDimension'
        dim = etree.Element("Dimension", name=self.name, type=type, description=self.description,
                            foreignKey=self.foreign_key)
        for item in config.mondrian_dimension_templates()[self.template]:
            hierarchy = etree.SubElement(dim, "Hierarchy", allMemberName=f'All {self.name.lower()}s', hasAll="true",
                                         name=item.name)
            etree.SubElement(hierarchy, "Table", schema=item.table[0], name=item.table[1])
            for level in item.levels:
                etree.SubElement(hierarchy, "Level", name=level.name, column=level.column, type=level.type,
                                 levelType=level.level_type, uniqueMembers=str(level.unique_members).lower())
        return dim


class AbstractMeasure():
    def __init__(self, name, description, format_string):
        """
        A common base class for MondrianMeasure and MondrianCalculatedMember.
        Args:
            name: How the metric is displayed in front-ends, e.g. "Revenue after cancellations".
            description: A meaningful business definition of the metric.
            format_string: It is used for formatString in Mondrian.
        """
        self.name = name
        self.description = description
        self.format_string = format_string

    def __repr__(self) -> str:
        return f'<MondrianAbstractMeasure "{self.name}">'


class DataType(enum.EnumMeta):
    NUMERIC = 'Numeric'
    INTEGER = 'Integer'


class Measure(AbstractMeasure):
    def __init__(self, name: str, description: str, column_name: str, aggregator: Aggregation, data_type: DataType,
                 format_string: NumberFormat):
        """
        A Mondrian Measure object.
        Args:
            name: How the metric is displayed in front-ends, e.g. "Revenue after cancellations".
            description: A meaningful business definition of the metric.
            column_name: The column that the aggregation is based on.
            aggregator: The aggregation method to use.
            data_type: Numeric or Integer. Default is Numeric. Integer for `count` and `distinct-count`.
            format_string: It is used for formatString in Mondrian' Measure.
        """
        super().__init__(name=name, description=description, format_string=format_string)
        self.column_name = column_name
        self.aggregator = aggregator
        self.data_type = data_type

    def __repr__(self) -> str:
        return f'<MondrianMeasure "{self.name}": {self.aggregator}>'

    def get_xml_element(self):
        """
        Returns an XML representation of this object.
        """
        measure = etree.Element("Measure", name=self.name, description=self.description,
                                column=self.column_name, aggregator=self.aggregator,
                                formatString=self.format_string, datatype=self.data_type)
        return measure


class CalculatedMember(AbstractMeasure):

    def __init__(self, name: str, description: str, formula: str, format_string):
        """
        A metric that is derived from other metrics.
        Args:
            name: How the metric is displayed in front-ends, e.g. "Revenue after cancellations"
            description: A meaningful business definition of the metric
            formula: How to compute the metric. e.g. [Measures].[Metric A] + [Measures].[Metric B]
            format_string: How to format the metric.
       """
        super().__init__(name=name, description=description, format_string=format_string)
        self.formula = formula

    def __repr__(self) -> str:
        return f'<MondrianCalculatedMember "{self.name}": {self.formula}>'

    def get_xml_element(self):
        """
        Returns an XML representation of this object.
        """
        measure = etree.Element("CalculatedMember", name=self.name, dimension="Measures",
                                description=self.description)
        hierarchy = etree.SubElement(measure, "Formula")
        hierarchy.text = self.formula

        etree.SubElement(measure, "CalculatedMemberProperty", name="FORMAT_STRING",
                         value=self.format_string)
        return measure


class Cube():
    def __init__(self, data_set: DataSet, schema_fact_table: str):
        """
        A cube is a named collection of measures and dimensions.
        For more information see https://mondrian.pentaho.com/documentation/schema.php#Cube
        Args:
            data_set: An entity with its metrics and recursively linked entities.
            schema_fact_table: The schema name for mondrian fact tables, e.g. "af_dim".
        """
        self.data_set = data_set
        self.schema_fact_table = schema_fact_table
        self.name = data_set.entity.name
        self.description = data_set.entity.description
        self.cube_dimensions = []
        self.measures = []
        self.calculated_members = []

        self.add_dimensions()
        self.add_measures()
        self.add_calculated_members()

    def add_dimensions(self):
        """
        Add Dimensions to a Mondrian Cube, e.g. PrivateDimension, LinkedDimension.
        """
        for path, attributes in self.data_set.connected_attributes(
                include_personal_data=config.include_personal_data_in_mondrian_schema()).items():
            for attribute in attributes:
                if attribute.type != Type.ARRAY \
                    and (not config.exclude_high_cardinality_dimension_from_mondrian_schema() or
                         (config.exclude_high_cardinality_dimension_from_mondrian_schema()
                          and not attribute.high_cardinality)):
                    name = generate_attribute_name(attribute, path)
                    if attribute.type in config.mondrian_dimension_templates():
                            dimension = TemplatedDimension(name=name,
                                                           description=attribute.description,
                                                           foreign_key=generate_fk_from_attribute(attribute, path),
                                                           template=attribute.type)
                    elif not path:
                        dimension = PrivateDimension(name=name,
                                                     description=attribute.description,
                                                     column_name=attribute.column_name)
                        dimension.add_hierarchy()
                    else:
                        entity = path[-1].target_entity
                        dimension = LinkedDimension(name=name,
                                                    description=attribute.description,
                                                    column_name=attribute.column_name,
                                                    foreign_key=generate_mondrian_fact_table_fk(self.data_set,
                                                                                                path),
                                                    primary_key=entity.pk_column_name,
                                                    table_name=entity.table_name,
                                                    schema_name=entity.schema_name)
                    self.cube_dimensions.append(dimension)

    def add_measures(self):
        """
        Add Measures to a Mondrian Cube.
        """
        for name, metric in self.data_set.metrics.items():
            if isinstance(metric, SimpleMetric):
                if metric.aggregation in [Aggregation.COUNT, Aggregation.DISTINCT_COUNT]:
                    data_type = DataType.INTEGER
                else:
                    data_type = DataType.NUMERIC
                measure = Measure(name=metric.name,
                                  description=metric.description,
                                  column_name=metric.column_name,
                                  aggregator=metric.aggregation,
                                  data_type=data_type,
                                  format_string=metric.number_format)
                self.measures.append(measure)

    def add_calculated_members(self):
        """
        Add CalculatedMembers to a Mondrian Cube.
        """
        for name, metric in self.data_set.metrics.items():
            if isinstance(metric, ComposedMetric):
                formula = metric.formula_template.format(
                    *[f'[{metric.name}]' for metric in metric.parent_metrics]).replace('[', '[Measures].[')
                calculated_member = CalculatedMember(name=metric.name,
                                                     description=metric.description,
                                                     formula=formula,
                                                     format_string=metric.number_format)
                self.calculated_members.append(calculated_member)

    def get_xml_element(self):
        """
        Returns an XML representation of this object.
        """
        cube = etree.Element("Cube", name=self.name, description=self.description,
                             defaultMeasure=list(self.data_set.metrics.keys())[0])
        table = etree.SubElement(cube, "Table", schema=self.schema_fact_table,
                                 name=self.data_set.entity.table_name + '_fact')

        subtag = table

        for item in self.cube_dimensions:
            dim = item.get_xml_element()
            subtag.addnext(dim)
            subtag = dim

        for item in self.measures:
            measure = item.get_xml_element()
            subtag.addnext(measure)
            subtag = measure

        for item in self.calculated_members:
            calculated_member = item.get_xml_element()
            subtag.addnext(calculated_member)
            subtag = calculated_member

        return cube


class MondrianSchema():
    def __init__(self, name: str):
        """
        A schema defines a multi-dimensional database.
        For more information see https://mondrian.pentaho.com/documentation/schema.php#What_is_a_schema
        Args:
            name: Name of this schema.
        """
        self.name = name

    def create_schema(self):
        """
        Returns an XML file which is the representation of the Mondrian Schema.
        For more information see https://mondrian.pentaho.com/documentation/schema.php#Schema_files
        """
        root = etree.XML(f'''\
<?xml version="1.0"?>
<Schema name="{self.name}"> 
</Schema>
''')

        for data_set in config.data_sets():
            cube = Cube(data_set=data_set, schema_fact_table=config.mondrian_schema()["fact_table_schema_name"])
            root.append(cube.get_xml_element())

        output_path = config.mondrian_schema()["schema_file_dir"] / 'schema.xml'
        parser = etree.XMLParser(remove_blank_text=True)
        result_schema = BytesIO(etree.tostring(root))
        tree = etree.parse(result_schema, parser)
        tree.write(output_path.absolute().as_uri(), encoding='utf-8', pretty_print=True, xml_declaration=True)
