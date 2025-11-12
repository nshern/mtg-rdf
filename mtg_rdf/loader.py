import docker

ALLOWD_DBS=['graphdb']

class Loader:

    def __init__(self, db, container_config = {}):
        if db not in ALLOWD_DBS:
            raise ValueError(f"Database '{db}' is not supported. Supported databases are: {', '.join(ALLOWD_DBS)}")
        else:
            self.db = db
        self.client = docker.from_env()
        self.container_config = container_config

    def run_container(self, image, name, ports, environment):
        try:
            container = self.client.containers.run(
                image=self.container_config["image"],
                name=self.container_config["name"],
                ports=self.container_config["ports"],
                environment=self.container_config["environment"],
                detach=True
            )
            print(f"Container '{name}' started successfully.")
            return container
        except Exception as e:
            print(f"Error starting container '{name}': {e}")
            return None

