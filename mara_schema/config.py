import functools
import pathlib

from .schema import DataSet, Type


@functools.lru_cache(maxsize=None)
def data_sets() -> [DataSet]:
    """Returns all available data_sets."""
    from examples.data_sets import data_sets
    return data_sets()


def mondrian_schema():
    """Returns configuration for Mondrian schema.
    schema_name: This will appear in Mondrian's schema file as the name of the schema. It is recommended use the
        company name.
    fact_table_schema_name: The schema name in database for mondrian fact tables.
    schema_file_dir: The directory to store mondrian schema file.
    """
    return {
        "schema_name": "CompanyXYZ",
        "fact_table_schema_name": "af_dim",
        "schema_file_dir": pathlib.Path('./app/mondrian')
            }


def exclude_high_cardinality_dimension_from_mondrian_schema():
    """If high cardinality dimension is excluded in mondrian schema. """
    return True


def include_personal_data_in_mondrian_schema():
    """If personal data is included in mondrian schema as dimension. """
    return False


def mondrian_dimension_templates() -> {Type: 'Hierarchy'}:
    """Attribute with specific types (e.g. Type.DATE, Type.DURATION) can be created as Mondrian Dimension with template.
    """
    from .mondrian_schema_generation import Hierarchy

    date_hierarchies = []

    hierarchy_month = Hierarchy(
        name='By month')
    hierarchy_month.add_table(schema_name='time', name='day')
    hierarchy_month.add_level(
        name='Year', column='year_id', name_column='year_name', type='Integer', level_type='TimeYears',
        unique_members=True)
    hierarchy_month.add_level(
        name='Quarter', column='quarter_id', name_column='quarter_name', type='Integer',
        level_type='TimeQuarters',
        unique_members=True)
    hierarchy_month.add_level(
        name='Month', column='month_id', name_column='month_name', type='Integer',
        level_type='TimeMonths',
        unique_members=True)
    hierarchy_month.add_level(
        name='Day', column='day_id', name_column='day_name', type='Integer',
        level_type='TimeDays',
        unique_members=True)
    date_hierarchies.append(hierarchy_month)

    hierarchy_week = Hierarchy(
        name='By week')
    hierarchy_week.add_table(schema_name='time', name='day')
    hierarchy_week.add_level(
        name='Year', column='iso_year_id', type='Integer', level_type='TimeYears',
        unique_members=True)
    hierarchy_week.add_level(
        name='Week', column='week_id', name_column='week_name', type='Integer',
        level_type='TimeWeeks',
        unique_members=True)
    hierarchy_week.add_level(
        name='Day', column='day_id', name_column='day_name', type='Integer', level_type='TimeDays',
        unique_members=True)
    date_hierarchies.append(hierarchy_week)

    duration_hierarchies = []

    hierarchy_month = Hierarchy(
        name='By month')
    hierarchy_month.add_table(schema_name='time', name='duration')
    hierarchy_month.add_level(
        name='Days', column='days', name_column='days_name', type='Integer', unique_members=True)
    hierarchy_month.add_level(
        name='Months', column='months', name_column='months_name', type='Integer',
        unique_members=True)
    hierarchy_month.add_level(
        name='Half years', column='half_years', name_column='half_years_name', type='Integer',
        unique_members=True)
    hierarchy_month.add_level(
        name='Years', column='years', name_column='years_name', type='Integer',
        unique_members=True)
    duration_hierarchies.append(hierarchy_month)

    hierarchy_week = Hierarchy(
        name='By week')
    hierarchy_week.add_table(schema_name='time', name='duration')
    hierarchy_week.add_level(
        name='Days', column='days', name_column='days_name', type='Integer', unique_members=True)
    hierarchy_week.add_level(
        name='Weeks', column='weeks', name_column='weeks_name', type='Integer',
        unique_members=True)
    hierarchy_week.add_level(
        name='Four weeks', column='four_weeks', name_column='four_weeks_name', type='Integer',
        unique_members=True)
    hierarchy_week.add_level(
        name='Years', column='years', name_column='years_name', type='Integer',
        unique_members=True)
    duration_hierarchies.append(hierarchy_week)

    return {Type.DATE: date_hierarchies, Type.DURATION: duration_hierarchies}
