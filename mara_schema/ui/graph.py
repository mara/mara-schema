import graphviz
from mara_page.xml import _

from ..data_set import DataSet
from ..metric import ComposedMetric

link_color_ = '#0275d8'
font_size_ = '10.5px'
line_color_ = '#888888'
edge_arrow_size_ = '0.7'


def overview_graph():
    from .. import config
    from .views import data_set_url

    all_entities = set()

    for data_set in config.data_sets():
        all_entities.update(data_set.entity.connected_entities())

    graph = graphviz.Digraph(engine='neato', graph_attr={})

    for entity in all_entities:
        data_set = entity.data_set

        graph.node(name=entity.name,
                   label=entity.name.replace(' ', '\n'),
                   fontname=' ',
                   fontsize=font_size_,
                   fontcolor=link_color_ if data_set else '#222222',
                   href=data_set_url(data_set) if data_set else None,
                   color='transparent',
                   tooltip=entity.description)

        for entity_link in entity.entity_links:
            label = entity_link.prefix.lower().replace(entity_link.target_entity.name.lower(),'').title()
            graph.edge(entity.name,
                       entity_link.target_entity.name,
                       headlabel=label.replace(' ', '\n') if label else None,
                       labelfloat='true',
                       labeldistance='2.5',
                       labelfontsize='9.0',
                       fontcolor='#cccccc',
                       arrowsize=edge_arrow_size_,
                       color=line_color_)

    return _render_graph(graph)


def data_set_graph(data_set: DataSet) -> str:
    from .views import data_set_url

    paths = data_set.paths_to_connected_entities()
    if not paths:
        return ''

    graph = graphviz.Digraph(engine='neato', graph_attr={})

    graph.node(name='root',
               label=data_set.entity.name.replace(' ', '\n'),
               fontname=' ',
               fontsize=font_size_,
               color='#888888',
               height='0.1',
               fontcolor='#222222',
               style='dotted',
               shape='rectangle',
               tooltip=data_set.entity.description
               )

    for path in paths:
        entity_link = path[-1]

        data_set = entity_link.target_entity.data_set
        graph.node(name=str(path),
                   label=entity_link.target_entity.name.replace(' ', '\n'),
                   fontname=' ',
                   fontsize=font_size_,
                   color='transparent',
                   height='0.1',
                   href=data_set_url(data_set) if data_set else None,
                   fontcolor=link_color_ if data_set else None,
                   tooltip=entity_link.target_entity.description
                   )

        label = entity_link.prefix.lower().replace(entity_link.target_entity.name.lower(),'').title()
        graph.edge('root' if len(path) == 1 else str(path[:-1]), str(path),
                   color=line_color_,
                   headlabel=label.replace(' ', '\n') if label else None,
                   labelfloat='true',
                   labeldistance='2.5',
                   labelfontsize='9.0',
                   fontcolor='#cccccc',
                   arrowsize=edge_arrow_size_)

    return _render_graph(graph)


def metrics_graph(data_set: DataSet) -> str:
    graph = graphviz.Digraph(engine='dot', graph_attr={'rankdir': 'TD',
                                                       'ranksep': '0.2',
                                                       'nodesep': '0.15',
                                                       'splines': 'true'
                                                       })

    connected_metrics = set()
    for metric in data_set.metrics.values():
        if isinstance(metric, ComposedMetric):
            connected_metrics.add(metric)
            for parent_metric in metric.parent_metrics:
                connected_metrics.add(parent_metric)
                graph.edge(parent_metric.name,
                           metric.name,
                           color=line_color_,
                           arrowsize=edge_arrow_size_)

    for metric in connected_metrics:
        graph.node(name=metric.name,
                   label=metric.name.replace(' ', '\n'),
                   fontname=' ',
                   fontcolor='#222222',
                   fontsize=font_size_,
                   color='transparent',
                   height='0.1',
                   tooltip=f'{metric.description}\n\n{metric.display_formula()}')
    return _render_graph(graph)


def _render_graph(graph: graphviz.Digraph) -> str:
    try:
        return graph.pipe('svg').decode('utf-8')
    except graphviz.backend.ExecutableNotFound as e:
        import uuid
        # This exception occurs when the graphviz tools are not found.
        # We use here a fallback to client-side rendering using the javascript library d3-graphviz.
        graph_id = f'dependency_graph_{uuid.uuid4().hex}'
        escaped_graph_source = graph.source.replace("`","\\`")
        return str(_.div(id=graph_id)[
            _.tt(style="color:red")[str(e)],
        ]) + str(_.script[
            f'div=d3.select("#{graph_id}");',
            'graph=div.graphviz();',
            'div.text("");',
            f'graph.renderDot(`{escaped_graph_source}`);',
        ])
