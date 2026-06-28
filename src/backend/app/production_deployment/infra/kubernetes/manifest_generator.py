from dataclasses import dataclass, field
import json
import os
import yaml


@dataclass
class ContainerSpec:
    name: str
    image: str
    port: int
    env_vars: dict[str, str] = field(default_factory=dict)
    resources: dict[str, dict[str, str]] = field(default_factory=dict)
    liveness_probe_path: str = "/health"
    readiness_probe_path: str = "/health"


@dataclass
class ServiceSpec:
    name: str
    port: int
    target_port: int
    service_type: str = "ClusterIP"


@dataclass
class VolumeClaimSpec:
    name: str
    size: str = "10Gi"
    access_modes: list[str] = field(default_factory=lambda: ["ReadWriteOnce"])


@dataclass
class K8sDeploymentTemplate:
    name: str
    namespace: str = "athena"
    replicas: int = 2
    containers: list[ContainerSpec] = field(default_factory=list)
    services: list[ServiceSpec] = field(default_factory=list)
    volume_claims: list[VolumeClaimSpec] = field(default_factory=list)
    labels: dict[str, str] = field(default_factory=dict)
    annotations: dict[str, str] = field(default_factory=dict)
    strategy: str = "RollingUpdate"

    def add_container(self, container: ContainerSpec) -> None:
        self.containers.append(container)

    def add_service(self, service: ServiceSpec) -> None:
        self.services.append(service)

    def to_deployment_dict(self) -> dict:
        containers = []
        for c in self.containers:
            container_def: dict = {
                "name": c.name,
                "image": c.image,
                "ports": [{"containerPort": c.port}],
                "env": [{"name": k, "value": v} for k, v in c.env_vars.items()],
                "livenessProbe": {
                    "httpGet": {"path": c.liveness_probe_path, "port": c.port},
                    "initialDelaySeconds": 10,
                    "periodSeconds": 15,
                },
                "readinessProbe": {
                    "httpGet": {"path": c.readiness_probe_path, "port": c.port},
                    "initialDelaySeconds": 5,
                    "periodSeconds": 10,
                },
            }
            if c.resources:
                container_def["resources"] = c.resources
            containers.append(container_def)

        return {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": self.name,
                "namespace": self.namespace,
                "labels": self.labels,
                "annotations": self.annotations,
            },
            "spec": {
                "replicas": self.replicas,
                "strategy": {"type": self.strategy},
                "selector": {"matchLabels": {"app": self.name}},
                "template": {
                    "metadata": {"labels": {"app": self.name}},
                    "spec": {"containers": containers},
                },
            },
        }

    def to_service_dicts(self) -> list[dict]:
        service_dicts = []
        for svc in self.services:
            service_dicts.append({
                "apiVersion": "v1",
                "kind": "Service",
                "metadata": {
                    "name": svc.name,
                    "namespace": self.namespace,
                    "labels": self.labels,
                },
                "spec": {
                    "type": svc.service_type,
                    "ports": [{"port": svc.port, "targetPort": svc.target_port}],
                    "selector": {"app": self.name},
                },
            })
        return service_dicts

    def to_pvc_dicts(self) -> list[dict]:
        pvc_dicts = []
        for pvc in self.volume_claims:
            pvc_dicts.append({
                "apiVersion": "v1",
                "kind": "PersistentVolumeClaim",
                "metadata": {"name": pvc.name, "namespace": self.namespace},
                "spec": {
                    "accessModes": pvc.access_modes,
                    "resources": {"requests": {"storage": pvc.size}},
                },
            })
        return pvc_dicts

    def to_yaml(self) -> str:
        return yaml.dump(self.to_deployment_dict(), default_flow_style=False, sort_keys=False)

    def to_json(self) -> str:
        return json.dumps(self.to_deployment_dict(), indent=2)


def get_default_k8s_deployment(namespace: str = "athena") -> K8sDeploymentTemplate:
    template = K8sDeploymentTemplate(
        name="athena-backend",
        namespace=namespace,
        replicas=2,
        labels={"app": "athena", "component": "backend"},
    )

    template.add_container(
        ContainerSpec(
            name="backend",
            image="athena-backend:latest",
            port=8000,
            env_vars={"ENV": "production"},
            resources={
                "requests": {"cpu": "250m", "memory": "256Mi"},
                "limits": {"cpu": "500m", "memory": "512Mi"},
            },
            liveness_probe_path="/health",
            readiness_probe_path="/health",
        )
    )

    template.add_service(
        ServiceSpec(name="athena-backend", port=80, target_port=8000)
    )

    return template


def generate_k8s_manifests(output_dir: str, namespace: str = "athena") -> None:
    os.makedirs(output_dir, exist_ok=True)

    template = get_default_k8s_deployment(namespace)

    with open(os.path.join(output_dir, "deployment.yaml"), "w", encoding="utf-8") as f:
        f.write(template.to_yaml())

    services = template.to_service_dicts()
    if services:
        with open(os.path.join(output_dir, "service.yaml"), "w", encoding="utf-8") as f:
            f.write(yaml.dump_all(services, default_flow_style=False, sort_keys=False))

    pvcs = template.to_pvc_dicts()
    if pvcs:
        with open(os.path.join(output_dir, "pvc.yaml"), "w", encoding="utf-8") as f:
            f.write(yaml.dump_all(pvcs, default_flow_style=False, sort_keys=False))
