"""Small hand-wired dependency-injection container for the application."""

from pos.application.facade import PosFacade
from pos.domain.factories import EvaluationFactory, RubricEvaluationFactory
from pos.domain.ports import (
    CriterionRepository,
    EvaluationRepository,
    ResultExporter,
    StudentRepository,
)
from pos.domain.services import (
    ResultCalculationStrategy,
    StudentResultCalculator,
    WeightedAverageStrategy,
)
from pos.infrastructure.csv_exporter import CsvResultExporter
from pos.infrastructure.memory import (
    InMemoryCriterionRepository,
    InMemoryEvaluationRepository,
    InMemoryStudentRepository,
)


class ApplicationContainer:
    """Build the dependency graph and allow adapters to be replaced in tests."""

    def __init__(
        self,
        *,
        students: StudentRepository | None = None,
        criteria: CriterionRepository | None = None,
        evaluations: EvaluationRepository | None = None,
        evaluation_factory: EvaluationFactory | None = None,
        result_strategy: ResultCalculationStrategy | None = None,
        result_exporter: ResultExporter | None = None,
    ) -> None:
        self.students = students if students is not None else InMemoryStudentRepository()
        self.criteria = criteria if criteria is not None else InMemoryCriterionRepository()
        self.evaluations = (
            evaluations if evaluations is not None else InMemoryEvaluationRepository()
        )
        self.evaluation_factory = (
            evaluation_factory
            if evaluation_factory is not None
            else RubricEvaluationFactory()
        )
        self.result_strategy = (
            result_strategy if result_strategy is not None else WeightedAverageStrategy()
        )
        self.result_calculator = StudentResultCalculator(self.result_strategy)
        self.result_exporter = (
            result_exporter if result_exporter is not None else CsvResultExporter()
        )
        self.facade = PosFacade(
            students=self.students,
            criteria=self.criteria,
            evaluations=self.evaluations,
            evaluation_factory=self.evaluation_factory,
            result_calculator=self.result_calculator,
            result_exporter=self.result_exporter,
        )
