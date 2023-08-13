import logging
from functools import cached_property
from typing import Any
import requests
from airflow.hooks.base import BaseHook
from docker import APIClient

log = logging.getLogger(__name__)

class PortainerHook(BaseHook):
    """
    Interact with a Docker Daemon via Portainer..

    This class provides a thin wrapper around the ``docker.APIClient``.

    .. seealso::
        - `Docker SDK: Low-level API <https://docker-py.readthedocs.io/en/stable/api.html?low-level-api>`_

    :param portainer_conn_id: portainer credentials
    :param endpoint_id: docker endpoint id as in portainer
    :param version: The version of the API to use. Needs to be explicitly set (otherwise auth does not work properly)
    :param timeout: Default timeout for API calls, in seconds.
    """

    conn_name_attr = "portainer_conn_id"
    default_conn_name = "portainer"
    conn_type = "http"
    hook_name = "portainer"

    def __init__(
            self,
            portainer_conn_id: str | None = default_conn_name,
            endpoint_id: int  = 0,
            version: str | None = "1.35",
            timeout: int = 30,
    ):
        super().__init__()
        self.portainer_conn_id = portainer_conn_id
        conn = self.get_connection(portainer_conn_id)
        self._portainer_base_url = f"{conn.schema}://{conn.host}:{conn.port}"
        self.__base_url = f"{self._portainer_base_url}/api/endpoints/{endpoint_id}/docker"
        self.__version = version
        self.__timeout = timeout
        self.client = None

    @cached_property
    def api_client(self) -> APIClient:
        """Create connection to docker host and return ``docker.APIClient`` (cached)."""
        self.auth_header = self._do_portainer_login()
        client = APIClient(
            base_url=self.__base_url, version=self.__version, tls=True, timeout=self.__timeout
        )
        if 'HttpHeaders' in client._general_configs:
            client._general_configs['HttpHeaders'].update(self.auth_header)
        else:
            client._general_configs.update({
                'HttpHeaders': self.auth_header
            })
        return client


    @classmethod
    def get_ui_field_behaviour(cls) -> dict[str, Any]:
        """Returns custom field behaviour."""
        return {
            "relabeling": {
                "host": "Portainer host",
                "login": "Username",
            },
        }

    def _do_portainer_login(self) -> dict[str, str]:
        conn = self.get_connection(self.portainer_conn_id)
        login = {
            'username': conn.login,
            'password': conn.password,
        }
        log.info(f"Logging in to portainer with {self.portainer_conn_id}")
        resp = requests.post(
            url=f"{self._portainer_base_url}/api/auth",
            json=login
        )
        resp.raise_for_status()
        return {
            'Authorization': f"Bearer {resp.json().get('jwt')}"
        }

    def get_conn(self) -> APIClient:
        """Create connection to docker host and return ``docker.APIClient`` (cached)."""
        return self.api_client

