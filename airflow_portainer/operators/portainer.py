
"""Implements Docker operator."""
from functools import cached_property

from airflow.models import BaseOperator
from airflow.providers.docker.operators.docker import stringify

from airflow.utils.context import Context
from docker import APIClient

from airflow_portainer.hooks.portainer import PortainerHook


class PortainerOperator(BaseOperator):
    """Execute a command inside a docker container via portainer. """
    NO_IMAGE = ""

    def __init__(
        self, portainer_conn_id: str, endpoint_id: int, timeout: int,
            container_name: str, command: str,  user: str, **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.portainer_conn_id = portainer_conn_id
        self.endpoint_id = endpoint_id
        self.timeout = timeout
        self.container_name = container_name
        self.command = command
        self.user = user

    @cached_property
    def hook(self) -> PortainerHook:
        """Create and return an PortainerHook (cached)."""
        return PortainerHook(
            portainer_conn_id=self.portainer_conn_id,
            endpoint_id=self.endpoint_id,
            version="1.35",
            timeout=self.timeout,
        )

    @property
    def cli(self) -> APIClient:
        return self.hook.api_client


    def execute(self, context: Context):
        try:
            self.log.info(f"Config of apiclient: {self.cli._general_configs}")
            container = self.cli.containers(filters={"name": self.container_name})[0]
            exec = self.cli.exec_create(container["Id"], cmd = self.command, user=self.user)
            logstream = self.cli.exec_start(exec["Id"], stream=True)

            log_lines = []
            for log_chunk in logstream:
                log_chunk = stringify(log_chunk).strip()
                log_lines.append(log_chunk)
                self.log.info("%s", log_chunk)

        except Exception as e:
            self.log.error("Error starting ", exc_info=True, stack_info=True)
            raise e
