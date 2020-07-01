import abc
import enum


class Aggregation(enum.EnumMeta):
    """Aggregation methods for metrics"""
    SUM = 'sum'
    AVERAGE = 'avg'
    COUNT = 'count'
    DISTINCT_COUNT = 'distinct-count'


class NumberFormat(enum.EnumMeta):
    """How to format values"""
    STANDARD = 'Standard'
    CURRENCY = 'Currency'
    PERCENT = 'Percent'


class Metric(abc.ABC):
    def __init__(self, name: str, description: str, data_set: 'DataSet',
                 important_field: bool = False) -> None:
        """
        A numeric aggregation on columns of an entity table.

        Args:
            name: How the metric is displayed in front-ends, e.g. "Revenue after cancellations"
            description: A meaningful business definition of the metric
            important_field: It refers to key business metrics.
        """
        self.name = name
        self.description = description
        self.data_set = data_set
        self.important_field = important_field

    @abc.abstractmethod
    def display_formula(self):
        """Returns a documentation string for displaying the formula in the frontend"""
        pass


class SimpleMetric(Metric):
    def __init__(self, name: str, description: str, data_set: 'DataSet',
                 column_name: str, aggregation: Aggregation, important_field: bool = False,
                 number_format: NumberFormat = NumberFormat.STANDARD):
        """
        A metric that is computed as a direct aggregation on a entity table column
        Args:
            name: How the metric is displayed in front-ends, e.g. "Revenue after cancellations"
            description: A meaningful business definition of the metric
            data_set: The data set that contains the metric
            column_name: The column that the aggregation is based on
            aggregation: The aggregation method to use
            important_field: It refers to key business metrics.
            number_format: The way to format a string. Defaults to NumberFormat.STANDARD.
        """
        super().__init__(name, description, data_set)
        self.column_name = column_name
        self.aggregation = aggregation
        self.important_field = important_field
        self.number_format = number_format

    def __repr__(self) -> str:
        return f'<Metric "{self.name}": {self.display_formula()})>'

    def display_formula(self) -> str:
        return f"{self.aggregation}({self.column_name})"


class ComposedMetric(Metric):
    def __init__(self, name: str, description: str, data_set: 'DataSet',
                 parent_metrics: [Metric], formula_template: str, important_field: bool = False,
                 number_format: NumberFormat = NumberFormat.STANDARD) -> None:
        """
        A metric that is based on a list of simple metrics.
        Args:
            name: How the metric is displayed in front-ends, e.g. "Revenue after cancellations"
            description: A meaningful business definition of the metric
            data_set: The data set that contains the metric
            parent_metrics: The parent metrics that this metric is composed of
            formula_template: How to compose the parent metrics, with '{}' as placeholders
                Examples: '{} + {}', '{} / ({} + {})'
            important_field: It refers to key business metrics.
            number_format: The way to format a string. Defaults to NumberFormat.STANDARD.
        """
        super().__init__(name, description, data_set)
        self.parent_metrics = parent_metrics
        self.formula_template = formula_template
        self.important_field = important_field
        self.number_format = number_format

    def __repr__(self) -> str:
        return f'<ComposedMetric "{self.name}": {self.display_formula()}>'

    def display_formula(self) -> str:
        return self.formula_template.format(*[f'[{metric.name}]' for metric in self.parent_metrics])
