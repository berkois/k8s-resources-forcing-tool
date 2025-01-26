# Kubernetes Resource Injector

The Kubernetes Resource Injector is a tool designed to enforce best practices by automatically injecting default resource limits and requests into Kubernetes pods or deployments that lack explicit resource configurations. The tool is implemented in Python and integrates seamlessly with Kubernetes as a controller.

---

## **Features**

- Monitors pods and deployments for missing resource configurations.
- Injects default resource requests and limits when absent.
- Configurable default values via a Kubernetes ConfigMap.
- Runs continuously as a Kubernetes controller for real-time resource injection.
- Fully containerized and easy to deploy.

---

## **Getting Started**

### **Prerequisites**

1. **Kubernetes Cluster**: A running Kubernetes cluster with permissions to apply manifests.
2. **kubectl**: Installed and configured to interact with your Kubernetes cluster.

---

### **Setup Instructions**

#### **1. Download the Prebuilt Docker Image**

The tool's Docker image is prebuilt and available on Docker Hub. Pull the latest version:

```bash
docker pull berkois/k8s-resource-controller:latest
```

#### **2. Configure the Kubernetes Manifests**

- Modify `manifests/configmap.yaml` to set default resource values:

```yaml
data:
  DEFAULT_CPU_REQUEST: "500m"
  DEFAULT_MEMORY_REQUEST: "512Mi"
  DEFAULT_CPU_LIMIT: "1000m"
  DEFAULT_MEMORY_LIMIT: "1Gi"
```

- Ensure the `image` field in `manifests/deployment.yaml` points to the correct Docker image tag:

```yaml
containers:
  - name: resource-injector
    image: berkois/k8s-resource-controller:latest
```

#### **3. Apply the Kubernetes Manifests**

```bash
kubectl apply -f manifests/
```

---

## **Configuration**

The tool uses a ConfigMap (`manifests/configmap.yaml`) to define default resource values. You can modify the values as needed:

```yaml
data:
  DEFAULT_CPU_REQUEST: "500m"
  DEFAULT_MEMORY_REQUEST: "512Mi"
  DEFAULT_CPU_LIMIT: "1000m"
  DEFAULT_MEMORY_LIMIT: "1Gi"
```

After updating the ConfigMap, reapply it:

```bash
kubectl apply -f manifests/configmap.yaml
```

---

## **Usage**

Once deployed, the tool runs continuously as a Deployment. To view logs for the running controller:

```bash
kubectl logs -l app=resource-injector --namespace kube-system
```

---

## **Customization**

1. **Change Default Resource Values**: Edit the `ConfigMap` and apply changes:

   ```bash
   kubectl apply -f manifests/configmap.yaml
   ```

2. **Scale the Controller**: Update the `replicas` field in `manifests/deployment.yaml` and reapply the manifest:
   ```yaml
   replicas: 2 # Scale to 2 replicas
   ```
   ```bash
   kubectl apply -f manifests/deployment.yaml
   ```

---

## **Cleanup**

To remove the tool and its resources:

```bash
kubectl delete -f manifests/
```

---

## **Future Enhancements**

- Add support for additional resource types (e.g., StatefulSets).
- Include integration tests to verify Kubernetes interaction.
- Implement logging enhancements with structured formats.
