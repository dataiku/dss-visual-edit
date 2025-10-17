import os
from typing import Any
from behave.model import Scenario

from docker_helper import get_container_memory_percentage


class MemLimitStrategy:
    @staticmethod
    def name() -> str:
        raise NotImplementedError

    def should_restart_dss(self, scenario: Scenario, container: Any) -> bool:
        raise NotImplementedError


class PercentageStrategy(MemLimitStrategy):
    @staticmethod
    def name() -> str:
        return "percentage"

    def __init__(self, threshold_percentage: float):
        self.threshold_percentage = threshold_percentage

    def should_restart_dss(self, scenario: Scenario, container: Any) -> bool:
        return (
            get_container_memory_percentage(container=container)
            > self.threshold_percentage
        )


class NeverRestartStrategy(MemLimitStrategy):
    @staticmethod
    def name() -> str:
        return "never"

    def should_restart_dss(self, scenario: Scenario, container: Any) -> bool:
        return False


class AlwaysRestartStrategy(MemLimitStrategy):
    @staticmethod
    def name() -> str:
        return "always"

    def should_restart_dss(self, scenario: Scenario, container: Any) -> bool:
        return True


class ScenarioIntervalRestartStrategy(MemLimitStrategy):
    @staticmethod
    def name() -> str:
        return "scenario_interval"

    def __init__(self, interval: int = 5):
        self.scenario_count = 0
        self.interval = interval

    def should_restart_dss(self, scenario: Scenario, container: Any) -> bool:
        self.scenario_count += 1
        return self.scenario_count % self.interval == 0


def get_memlimit_strategy() -> MemLimitStrategy:
    memlimit_strategy = os.getenv("MEMLIMIT_STRATEGY", None)
    if memlimit_strategy == PercentageStrategy.name():
        threshold = int(os.getenv("MEMLIMIT_PERCENTAGE_THRESHOLD", 80))
        return PercentageStrategy(threshold_percentage=threshold)
    elif memlimit_strategy == NeverRestartStrategy.name():
        return NeverRestartStrategy()
    elif memlimit_strategy == AlwaysRestartStrategy.name():
        return AlwaysRestartStrategy()
    elif memlimit_strategy == ScenarioIntervalRestartStrategy.name():
        interval = int(os.getenv("MEMLIMIT_SCENARIO_INTERVAL", 5))
        return ScenarioIntervalRestartStrategy(interval)
    else:
        raise ValueError(f"Unknown memory limit strategy: {memlimit_strategy}")
