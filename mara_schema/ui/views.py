"""Documentation of data sets and entities"""

import functools
import re
from html import escape

import flask
import unicodedata
from mara_page import acl, navigation, response, bootstrap, _, html

from ..data_set import DataSet

# The flask blueprint that does
blueprint = flask.Blueprint('mara_schema', __name__, static_folder='static',
                            template_folder='templates', url_prefix='/schema')

# Defines an ACL resource (needs to be handled by the application)
acl_resource_schema = acl.AclResource(name='Schema')


def data_set_url(data_set: DataSet) -> str:
    return flask.url_for('mara_schema.data_set_page', id=data_set.id())


_slugify_strip_re = re.compile(r'[^\w\s-]')
_slugify_hyphenate_re = re.compile(r'[-\s]+')


# from https://github.com/django/django/blob/0382ecfe020b4c51b4c01e4e9a21892771e66941/django/utils/text.py
# Under BSD license
def slugify(value, allow_unicode=False):
    """
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(_slugify_strip_re, '', value.lower())
    return re.sub(_slugify_hyphenate_re, '-', value).strip('-_')


def schema_navigation_entry() -> navigation.NavigationEntry:
    """Defines a part of the navigation tree (needs to be handled by the application).

    Returns:
        A mara NavigationEntry object.

    """
    from .. import config

    return navigation.NavigationEntry(
        label='Data sets', icon='book',
        description='Documentation of attributes and metrics of all data sets',
        children=[navigation.NavigationEntry(label='Overview', icon='list',
                                             uri_fn=lambda: flask.url_for('mara_schema.index_page'))]
                 + [navigation.NavigationEntry(label=data_set.name, icon='book',
                                               description=data_set.entity.description,
                                               uri_fn=lambda data_set=data_set: flask.url_for(
                                                   'mara_schema.data_set_page', id=data_set.id()))
                    for data_set in config.data_sets()])


@blueprint.route('')
@acl.require_permission(acl_resource_schema)
def index_page() -> response.Response:
    """Renders the overview page"""
    from .. import config

    return response.Response(

        html=[
            bootstrap.card(
                header_left='Entities & their relations',
                body=html.asynchronous_content(flask.url_for('mara_schema.overview_graph'))),
            bootstrap.card(
                header_left='Data sets',
                body=bootstrap.table(
                    ['Name', 'Description'],
                    [_.tr[_.td[_.a(href=flask.url_for('mara_schema.data_set_page',
                                                      id=data_set.id()))[
                        escape(data_set.name)]],
                          _.td[_.i[escape(data_set.entity.description)]],
                     ] for data_set in config.data_sets()]),
            )],
        title='Data sets documentation',
        css_files=[flask.url_for('mara_schema.static', filename='schema.css')]
    )


@blueprint.route('/<id>')
@acl.require_permission(acl_resource_schema)
def data_set_page(id: str) -> response.Response:
    """Renders the pages for individual data sets"""
    from .. import config

    data_set = next((data_set for data_set in config.data_sets() if data_set.id() == id), None)
    if not data_set:
        flask.flash(f'Could not find data set "{id}"', category='warning')
        return flask.redirect(flask.url_for('mara_schema.index_page'))

    base_url = flask.url_for('mara_schema.data_set_sql_query', id=data_set.id())

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
                         for entity_link in path]],
                    [' &nbsp;&nbsp;', _.i[path[-1].description]] if path[-1].description else ''
                ]])
            for prefixed_name, attribute in attributes.items():
                attribute_link_id = slugify(f'attribute {path[-1].target_entity.name if path else ""} {attribute.name}')
                rows.append(_.tr(id=attribute_link_id)[
                                _.td[
                                    escape(prefixed_name),
                                    ' ',
                                    _.a(class_='anchor-link-sign',
                                        href=f'#{attribute_link_id}')['¶'],

                                ],
                                _.td[[_.i[escape(attribute.description)]] +
                                     ([' (', _.a(href=attribute.more_url)['more...'], ')']
                                      if attribute.more_url else [])],
                                _.td[_.tt[escape(
                                    f'{path[-1].target_entity.table_name + "." if path else ""}{attribute.column_name}')]]])
        return rows

    def metrics_rows(data_set: DataSet) -> []:
        rows = []
        for metric in data_set.metrics.values():
            metric_link_id = slugify(f'metric {metric.name}')

            rows.append([_.tr(id=metric_link_id)[
                            _.td[
                                escape(metric.name),
                                ' ',
                                _.a(class_='anchor-link-sign',
                                    href=f'#{metric_link_id}')['¶'],

                            ],
                            _.td[[_.i[escape(metric.description)]] +
                                 ([' (', _.a(href=metric.more_url)['more...'], ')'] if metric.more_url else [])
                                 ],
                            _.td[_.code[escape(metric.display_formula())]]
                        ]])
        return rows

    return response.Response(
        html=[bootstrap.card(
            header_left=_.i[escape(data_set.entity.description)],
            body=[
                _.p['Entity table: ',
                    _.code[escape(f'{data_set.entity.schema_name}.{data_set.entity.table_name}')]],
                html.asynchronous_content(flask.url_for('mara_schema.data_set_graph', id=data_set.id())),
            ]),
            bootstrap.card(
                header_left='Metrics',
                body=[
                    html.asynchronous_content(flask.url_for('mara_schema.metrics_graph', id=data_set.id())),
                    bootstrap.table(
                        ['Name', 'Description', 'Computation'],
                        metrics_rows(data_set)
                    ),
                ]),
            bootstrap.card(
                header_left='Attributes',
                body=bootstrap.table(["Name", "Description", "Column name"], attribute_rows(data_set))),
            bootstrap.card(
                header_left=['Data set sql query: &nbsp;',
                             [_.div(class_='form-check form-check-inline')[
                                  "&nbsp;&nbsp; ",
                                  _.label(class_='form-check-label')[
                                      _.input(class_="form-check-input param-checkbox", type="checkbox",
                                              value=param)[
                                          ''], ' ', param]]
                              for param in [
                                  'human readable columns',
                                  'pre-computed metrics',
                                  'star schema',
                                  'star_schema_transitive_fks',
                                  'personal data',
                                  'high cardinality attributes',
                              ]]],
                body=[_.div(id='sql-container')[html.asynchronous_content(base_url, 'sql-container')],
                      _.script['''
document.addEventListener('DOMContentLoaded', function() {
    DataSetSqlQuery("''' + base_url + '''");
});
''']])
        ],
        title=f'Data set "{data_set.name}"',
        js_files=[flask.url_for('mara_schema.static', filename='data-set-sql-query.js')],
        css_files=[flask.url_for('mara_schema.static', filename='mara-schema.css')],
    )


@blueprint.route('/<id>/_data_set_sql_query', defaults={'params': ''})
@blueprint.route('/<id>/_data_set_sql_query/<path:params>')
def data_set_sql_query(id: str, params: [str]) -> response.Response:
    from .. import config
    from ..sql_generation import data_set_sql_query

    params = set(params.split('/'))
    data_set = next((data_set for data_set in config.data_sets() if data_set.id() == id), None)
    if not data_set:
        return f'Could not find data set "{id}"'

    # using the engine of the default db from mara_pipelines.config.default_db_alias()
    engine = None
    try:
        # since mara_pipelines and mara_db is not a default requirement of module mara_schema,
        # we use a try/except clause
        import mara_db.sqlalchemy_engine
        import mara_pipelines.config
        engine = mara_db.sqlalchemy_engine.engine(mara_pipelines.config.default_db_alias())
    except ImportError or ModuleNotFoundError or NotImplementedError:
        pass

    sql = data_set_sql_query(data_set,
                             pre_computed_metrics='pre-computed metrics' in params,
                             human_readable_columns='human readable columns' in params,
                             personal_data='personal data' in params,
                             high_cardinality_attributes='high cardinality attributes' in params,
                             star_schema='star schema' in params,
                             star_schema_transitive_fks='star_schema_transitive_fks' in params,
                             engine=engine)
    return str(_.div[html.highlight_syntax(sql, 'sql')])


@blueprint.route('/_overview_graph')
@acl.require_permission(acl_resource_schema, do_abort=False)
@functools.lru_cache(maxsize=None)
def overview_graph() -> str:
    """Returns an graph of all the defined entities and data sets"""
    from .graph import overview_graph

    return overview_graph()


@blueprint.route('/<id>/_data_set_graph')
@acl.require_permission(acl_resource_schema)
def data_set_graph(id: str) -> str:
    """Renders a graph with all the linked entities of an individual data sets"""
    from .. import config
    from .graph import data_set_graph

    data_set = next((data_set for data_set in config.data_sets() if data_set.id() == id), None)
    if not data_set:
        return f'Could not find data set "{id}"'

    return data_set_graph(data_set)


@blueprint.route('/<id>/_metrics_graph')
@acl.require_permission(acl_resource_schema)
def metrics_graph(id: str) -> str:
    """Renders a visualization of all composed metrics of a data set"""
    from .. import config
    from .graph import metrics_graph

    data_set = next((data_set for data_set in config.data_sets() if data_set.id() == id), None)
    if not data_set:
        return f'Could not find data set "{id}"'

    return metrics_graph(data_set)
