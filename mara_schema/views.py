"""Documentation of data sets and entities"""

import functools
from html import escape

import flask
import mara_schema.schema
from mara_page import acl, navigation, response, bootstrap, _
from mara_page import html

from .schema import DataSet

# The flask blueprint that does
blueprint = flask.Blueprint('mara_schema', __name__, static_folder='static',
                            template_folder='templates', url_prefix='/metadata')

# Defines an ACL resource (needs to be handled by the application)
acl_resource_metadata = acl.AclResource(name='Metadata')


def data_set_id(data_set: DataSet) -> str:
    return escape(data_set.name.replace(' ', '-').lower())


def data_set_url(data_set: mara_schema.schema.DataSet) -> str:
    return flask.url_for('mara_schema.data_set_page', id=data_set_id(data_set))


def metadata_navigation_entry() -> navigation.NavigationEntry:
    """Defines a part of the navigation tree (needs to be handled by the application).

    Returns:
        A mara NavigationEntry object.

    """
    from .config import data_sets

    return navigation.NavigationEntry(
        label='Data sets documentation', icon='book',
        description='Documentation of attributes and metrics of all data sets',
        children=[navigation.NavigationEntry(label='Overview', icon='list',
                                             uri_fn=lambda: flask.url_for('mara_schema.index_page'))]
                 + [navigation.NavigationEntry(label=data_set.entity.name, icon='book',
                                               description=data_set.entity.description,
                                               uri_fn=lambda data_set=data_set: flask.url_for(
                                                   'mara_schema.data_set_page', id=data_set_id(data_set)))
                    for data_set in data_sets()])


@blueprint.route('')
@acl.require_permission(acl_resource_metadata)
def index_page() -> response.Response:
    """Renders the overview page"""
    from .config import data_sets

    return response.Response(

        html=[bootstrap.card(
            header_left='Entities & their relations',
            body=html.asynchronous_content(flask.url_for('mara_schema.overview_graph'))),
            bootstrap.card(
                header_left='Data sets',
                body=bootstrap.table(
                    ['Name', 'Description'],
                    [_.tr[_.td[_.a(href=flask.url_for('mara_schema.data_set_page',
                                                      id=data_set_id(data_set)))[
                        escape(data_set.name)]],
                          _.td[_.i[escape(data_set.entity.description)]],
                     ] for data_set in data_sets()]),
            )],
        title='Data sets documentation',
        css_files=[flask.url_for('mara_schema.static', filename='metadata.css')]
    )


@blueprint.route('/<id>')
@acl.require_permission(acl_resource_metadata)
def data_set_page(id: str) -> response.Response:
    """Renders the pages for individual data sets"""
    from .config import data_sets
    from .schema import generate_attribute_name

    data_set = next((data_set for data_set in data_sets() if data_set_id(data_set) == id), None)
    if not data_set:
        flask.flash(f'Could not find data set "{id}"', category='warning')
        return flask.redirect(flask.url_for('mara_schema.index_page'))

    def attribute_rows(data_set: DataSet) -> []:
        rows = []
        for path, attributes in data_set.connected_attributes().items():
            if path:
                rows.append(_.tr[_.td(colspan=3, style='border-top:none; padding-top: 20px;')[
                    [['→ ',
                      _.a(href=data_set_url(entity.data_set))[link_title] if entity.data_set else link_title,
                      ' &nbsp;']
                     for entity, link_title
                     in [(entity_link.target_entity, entity_link.prefix or entity_link.target_entity.name)
                         for entity_link in path]]
                ]])
            for attribute in attributes:
                rows.append(_.tr[_.td[escape(generate_attribute_name(attribute, path))],
                                _.td[_.i[escape(attribute.description)]],
                                _.td[escape(attribute.column_name)]])
        return rows

    return response.Response(
        html=[bootstrap.card(
            header_left=_.i[escape(data_set.entity.description)],
            body=[
                _.p['Entity table: ',
                    _.code[escape(f'{data_set.entity.schema_name}.{data_set.entity.table_name}')]],
                html.asynchronous_content(flask.url_for('mara_schema.data_set_graph', id=data_set_id(data_set))),
            ]),
            bootstrap.card(
                header_left='Metrics',
                body=[
                    html.asynchronous_content(flask.url_for('mara_schema.metrics_graph', id=data_set_id(data_set))),
                    bootstrap.table(
                        ['Name', 'Description', 'Computation'],
                        [[_.tr[
                              _.td[escape(metric.name)],
                              _.td[_.i[escape(metric.description)]],
                              _.td[_.code[escape(metric.display_formula())]]
                          ] for metric in data_set.metrics.values()]]),
                ]),
            bootstrap.card(
                header_left='Attributes',
                body=bootstrap.table(["Name", "Description", "Column name"], attribute_rows(data_set)))
        ],
        title=f'Data set "{data_set.name}"',
        css_files=[flask.url_for('mara_schema.static', filename='metadata.css')]
    )


@blueprint.route('/_overview_graph')
@acl.require_permission(acl_resource_metadata, do_abort=False)
@functools.lru_cache(maxsize=None)
def overview_graph() -> str:
    """Returns an graph of all the defined entities and data sets"""
    from .graph import overview_graph

    return overview_graph()


@blueprint.route('/<id>/_data_set_graph')
@acl.require_permission(acl_resource_metadata)
def data_set_graph(id: str) -> response.Response:
    """Renders a graph with all the linked entities of an individual data sets"""
    from .config import data_sets
    from .graph import data_set_graph

    data_set = next((data_set for data_set in data_sets() if data_set_id(data_set) == id), None)
    if not data_set:
        return f'Could not find data set "{id}"'

    return data_set_graph(data_set)


@blueprint.route('/<id>/_metrics_graph')
@acl.require_permission(acl_resource_metadata)
def metrics_graph(id: str) -> response.Response:
    """Renders a visualization of all composed metrics of a data set"""
    from .config import data_sets
    from .graph import metrics_graph

    data_set = next((data_set for data_set in data_sets() if data_set_id(data_set) == id), None)
    if not data_set:
        return f'Could not find data set "{id}"'

    return metrics_graph(data_set)
