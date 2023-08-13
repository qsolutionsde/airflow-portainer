# Airflow provider for portainer

## Operator 

````python
    PortainerOperator(task_id="task",
                      portainer_conn_id="portainer", endpoint_id=16, timeout=30,
                      container_name="container", command="...",
                      user="www-data")
````