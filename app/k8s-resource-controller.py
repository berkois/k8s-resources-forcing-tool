import os
import logging
from kubernetes import client, config, watch
from kubernetes.client.exceptions import ApiException

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Log to stdout
    ],
)

DEFAULT_CPU_REQUEST = os.getenv("DEFAULT_CPU_REQUEST", "500m")
DEFAULT_MEMORY_REQUEST = os.getenv("DEFAULT_MEMORY_REQUEST", "512Mi")
DEFAULT_CPU_LIMIT = os.getenv("DEFAULT_CPU_LIMIT", "1000m")
DEFAULT_MEMORY_LIMIT = os.getenv("DEFAULT_MEMORY_LIMIT", "1Gi")

def log_resource_limits(namespace, name, kind):
    """Log the resource requests and limits of a resource."""
    try:
        api = client.AppsV1Api() if kind == "Deployment" else client.CoreV1Api()
        resource = api.read_namespaced_deployment(name, namespace) if kind == "Deployment" else api.read_namespaced_pod(name, namespace)
        containers = resource.spec.template.spec.containers if kind == "Deployment" else resource.spec.containers

        for container in containers:
            requests = container.resources.requests or {}
            limits = container.resources.limits or {}
            logging.info(
                f"{kind} '{name}' in namespace '{namespace}' - "
                f"Container '{container.name}': Requests: {requests}, Limits: {limits}"
            )

    except ApiException as e:
        logging.error(f"Error fetching updated {kind} '{name}' in namespace '{namespace}': {e.reason}, {e.body}")

def patch_resource_limits(namespace, name, kind):
    try:
        api = client.AppsV1Api() if kind == "Deployment" else client.CoreV1Api()
        spec = api.read_namespaced_deployment(name, namespace).spec if kind == "Deployment" else api.read_namespaced_pod(name, namespace).spec

        resource = (api.read_namespaced_deployment(name, namespace) if kind == "Deployment"
                    else api.read_namespaced_pod(name, namespace))
        containers = (resource.spec.template.spec.containers if kind == "Deployment"
                      else resource.spec.containers)

        modified_containers = []
        for container in containers:
            container_patch = {"name": container.name, "image": container.image}
            if not container.resources.requests:
                logging.info(f"Missing requests for container '{container.name}' in {kind} '{name}' in namespace '{namespace}'. Adding defaults: CPU='{DEFAULT_CPU_REQUEST}', Memory='{DEFAULT_MEMORY_REQUEST}'.")
                logging.info(f"Current Resources.requests: {container.resources.requests}")

                container_patch["resources"] = container_patch.get("resources", {})
                container_patch["resources"]["requests"] = {
                    "cpu": DEFAULT_CPU_REQUEST,
                    "memory": DEFAULT_MEMORY_REQUEST,
                }
                logging.info(f"Setting default requests for container '{container.name}' in {kind} '{name}': {container_patch['resources']['requests']}")

            if not container.resources.limits:
                logging.info(f"Missing limits for container '{container.name}' in {kind} '{name}' in namespace '{namespace}'. Adding defaults: CPU='{DEFAULT_CPU_REQUEST}', Memory='{DEFAULT_MEMORY_REQUEST}'.")
                logging.info(f"Current Resources.limits: {container.resources.limits}")
                container_patch["resources"] = container_patch.get("resources", {})
                container_patch["resources"]["limits"] = {
                    "cpu": DEFAULT_CPU_LIMIT,
                    "memory": DEFAULT_MEMORY_LIMIT,
                }
                logging.info(f"Setting default limits for container '{container.name}' in {kind} '{name}': {container_patch['resources']['limits']}")

            if "resources" in container_patch:
                modified_containers.append(container_patch)

        if modified_containers:
            patch_body = {
                "spec": {
                    "template": {
                        "spec": {
                            "containers": modified_containers
                        }
                    }
                }
            }
            if kind == "Deployment":
                response = api.patch_namespaced_deployment(name, namespace, patch_body)
            else:
                response = api.patch_namespaced_pod(name, namespace, patch_body)

            logging.info(
                f"Successfully applied updates to {kind} '{name}' in namespace '{namespace}'."
            )
            log_resource_limits(namespace, name, kind)
        else:
            logging.info(f"No changes needed for {kind} '{name}' in namespace '{namespace}'.")

    except ApiException as e:
        logging.error(f"Error updating {kind} '{name}' in namespace '{namespace}': {e.reason}, {e.body}")
    except Exception as e:
        logging.error(f"Unexpected error while processing {kind} '{name}' in namespace '{namespace}': {str(e)}")


def monitor_resources():
    try:
        config.load_incluster_config()
        v1 = client.CoreV1Api()
        apps_v1 = client.AppsV1Api()
        w = watch.Watch()

        # monitor Pods
        logging.info("Starting to monitor Pods for resource limits/requests...")
        for event in w.stream(v1.list_pod_for_all_namespaces, timeout_seconds=60):
            obj = event['object']
            if event['type'] == "ADDED":
                patch_resource_limits(obj.metadata.namespace, obj.metadata.name, "Pod")

        # monitor Deployments
        logging.info("Starting to monitor Deployments for resource limits/requests...")
        for event in w.stream(apps_v1.list_deployment_for_all_namespaces, timeout_seconds=60):
            obj = event['object']
            if event['type'] == "ADDED":
                patch_resource_limits(obj.metadata.namespace, obj.metadata.name, "Deployment")

    except Exception as e:
        logging.error(f"Error during resource monitoring: {str(e)}")

if __name__ == "__main__":
    monitor_resources()
