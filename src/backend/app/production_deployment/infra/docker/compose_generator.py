from dataclasses import dataclass, field
import json
import os


@dataclass
class DockerServiceConfig:
    name: str
    image: str
    port: int
    internal_port: int
    health_endpoint: str = "/health"
    env_vars: dict[str, str] = field(default_factory=dict)
    volumes: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    restart: str = "unless-stopped"
    networks: list[str] = field(default_factory=list)


@dataclass
class DockerComposeTemplate:
    version: str = "3.8"
    services: list[DockerServiceConfig] = field(default_factory=list)
    networks: list[str] = field(default_factory=list)
    volumes: list[str] = field(default_factory=list)
    project_name: str = "athena"

    def add_service(self, service: DockerServiceConfig) -> None:
        self.services.append(service)

    def to_compose_dict(self) -> dict:
        compose: dict = {"version": self.version, "services": {}, "networks": {}, "volumes": {}}

        for network in self.networks:
            compose["networks"][network] = {"driver": "bridge"}

        for volume in self.volumes:
            compose["volumes"][volume] = {}

        for svc in self.services:
            service_def: dict = {
                "image": svc.image,
                "restart": svc.restart,
                "networks": svc.networks if svc.networks else ["default"],
            }

            if svc.port and svc.internal_port:
                service_def["ports"] = [f"{svc.port}:{svc.internal_port}"]

            if svc.env_vars:
                service_def["environment"] = svc.env_vars

            if svc.volumes:
                service_def["volumes"] = svc.volumes

            if svc.depends_on:
                service_def["depends_on"] = {}
                for dep in svc.depends_on:
                    service_def["depends_on"][dep] = {"condition": "service_healthy"}

            if svc.health_endpoint:
                service_def["healthcheck"] = {
                    "test": f"CMD curl -f http://localhost:{svc.internal_port}{svc.health_endpoint} || exit 1",
                    "interval": "10s",
                    "timeout": "5s",
                    "retries": 3,
                    "start_period": "10s",
                }

            compose["services"][svc.name] = service_def

        return compose

    def to_yaml(self) -> str:
        import yaml
        return yaml.dump(self.to_compose_dict(), default_flow_style=False, sort_keys=False)

    def to_json(self) -> str:
        return json.dumps(self.to_compose_dict(), indent=2)


def get_default_services() -> list[DockerServiceConfig]:
    return [
        DockerServiceConfig(
            name="backend",
            image="athena-backend:latest",
            port=8000,
            internal_port=8000,
            health_endpoint="/health",
            env_vars={"ENV": "production"},
            depends_on=["postgres", "redis"],
            networks=["athena"],
        ),
        DockerServiceConfig(
            name="postgres",
            image="postgres:16-alpine",
            port=5432,
            internal_port=5432,
            env_vars={},
            volumes=["pgdata:/var/lib/postgresql/data"],
            networks=["athena"],
        ),
        DockerServiceConfig(
            name="redis",
            image="redis:7-alpine",
            port=6379,
            internal_port=6379,
            env_vars={},
            volumes=["redis_data:/data"],
            networks=["athena"],
        ),
        DockerServiceConfig(
            name="minio",
            image="minio/minio:latest",
            port=9000,
            internal_port=9000,
            env_vars={},
            volumes=["minio_data:/data"],
            networks=["athena"],
        ),
    ]


def generate_compose_file(output_path: str) -> None:
    template = DockerComposeTemplate(
        project_name="athena",
        networks=["athena"],
        volumes=["pgdata", "redis_data", "minio_data"],
        services=get_default_services(),
    )

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    try:
        content = template.to_yaml()
    except ImportError:
        content = template.to_json()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)
