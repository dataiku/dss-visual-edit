import logging
import time
from typing import Any
import docker


logger = logging.getLogger(__name__)


def get_container_by_name(container_name):
    client = docker.from_env()
    containers = client.containers.list(filters={"name": container_name})
    if not containers:
        raise RuntimeError(f"No running container found with name '{container_name}'.")
    if len(containers) > 1:
        raise RuntimeError(f"Multiple containers found with name '{container_name}'.")
    return containers[0]


def get_container_memory_percentage(
    container: Any = None, container_name: str | None = None
) -> float:
    if container is None and container_name is None:
        raise ValueError("Either container or container_name must be provided.")

    if container is None:
        container = get_container_by_name(container_name)

    container_name = container.name
    container.reload()
    stats = container.stats(stream=False)
    mem_stats = stats.get("memory_stats", {})
    if mem_stats:
        usage = mem_stats.get("usage", 0)
        cache = mem_stats.get("stats", {}).get("cache", 0)
        limit = mem_stats.get("limit", 0)
        actual_usage = usage - cache
        if limit == 0:
            logger.warning(
                f"Memory limit is not set for container '{container_name}', cannot calculate percentage."
            )
            return 0
        return (actual_usage / limit) * 100
    else:
        raise RuntimeError("No memory stats available.")


def restart_container(container: Any = None, container_name: str | None = None) -> None:
    if container is None and container_name is None:
        raise ValueError("Either container or container_name must be provided.")

    if container is None:
        container = get_container_by_name(container_name)

    container_name = container.name
    container.restart()
    logger.info(f"Container '{container_name}' restarted.")
    while True:
        container.reload()
        health_status = container.attrs["State"].get("Health", {}).get("Status")

        if health_status == "healthy":
            logger.info(
                f"Container '{container_name}' is healthy, proceeding with tests."
            )
            break
        else:
            logger.info(
                f"Waiting for container '{container_name}' to become healthy (status={health_status})..."
            )

        time.sleep(2)
