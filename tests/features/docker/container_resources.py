import logging
import os
from abc import ABC, abstractmethod
from typing import Any, List

from behave.model import Scenario
from features.docker.utils import get_container_by_name, get_container_memory_percentage, restart_container

logger = logging.getLogger(__name__)


class ContainerResourceLimiter(ABC):
    def __init__(self, container: Any):
        self.container = container

    @staticmethod
    @abstractmethod
    def name() -> str:
        pass

    @abstractmethod
    def should_restart(self, scenario: Scenario) -> bool:
        pass


class MemPercentageLimiter(ContainerResourceLimiter):
    @staticmethod
    def name() -> str:
        return "percentage"

    def __init__(self, container: Any, threshold_percentage: float):
        super().__init__(container)
        self.threshold_percentage = threshold_percentage

        logger.info(f"Memory percentage limiter initialized with threshold {self.threshold_percentage}%.")

    def should_restart(self, scenario: Scenario) -> bool:
        percentage = get_container_memory_percentage(self.container)
        if percentage > self.threshold_percentage:
            logger.info(f"Memory usage {percentage:.2f}% exceeds threshold {self.threshold_percentage}%.")
            return True

        logger.info(f"Memory usage {percentage:.2f}% is within threshold {self.threshold_percentage}%.")
        return False


def _get_resource_limiters(container: Any) -> List[ContainerResourceLimiter]:
    resource_limiters: List[ContainerResourceLimiter] = []
    mem_limiter = os.getenv("MEM_LIMITER", None)
    if mem_limiter:
        if mem_limiter == MemPercentageLimiter.name():
            threshold = int(os.getenv("MEM_LIMITER_PERCENTAGE_THRESHOLD", "80"))
            resource_limiters.append(MemPercentageLimiter(container, threshold))
        else:
            logger.warning("Unknown memory limiter %s. Ignoring...", mem_limiter)

    return resource_limiters


class ContainerResourcesController:
    def __init__(self, container: Any, limiters: List[ContainerResourceLimiter]):
        self.container = container
        self.limiters = limiters

    def restart_if_needed(self, scenario: Scenario):
        if self.should_restart(scenario):
            logger.info("Restarting %s due to resource limits.", self.container.name)

            restart_container(self.container)
            return True

        return False

    def should_restart(self, scenario: Scenario) -> bool:
        return any(limiter.should_restart(scenario) for limiter in self.limiters)


class NoopResourcesController(ContainerResourcesController):
    def __init__(self):
        super().__init__(None, [])

    def restart_if_needed(self, scenario: Scenario):
        return False

    def should_restart(self, scenario: Scenario) -> bool:
        return False


def get_container_resources_controller(
    container_name: str, custom_limiters: List[ContainerResourceLimiter] = []
) -> ContainerResourcesController:
    if not container_name:
        raise ValueError("Container must be provided.")

    container = get_container_by_name(container_name)
    limiters = _get_resource_limiters(container)
    limiters.extend(custom_limiters)
    return ContainerResourcesController(container, limiters)
