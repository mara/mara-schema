import click


@click.command()
def create_mondrian_schema():
    """Re-generates the mondrian schema file from the data-set definitions"""
    from .mondrian_schema_generation import MondrianSchema
    from .config import mondrian_schema

    mondrian_schema = MondrianSchema(name=mondrian_schema()["schema_name"])
    mondrian_schema.create_schema()
