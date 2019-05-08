# Prepare namespaces for wca and workloads

```
kubectl create namespace kubecon-demo
kubectl apply -f ./manifests_demo/namespace.yaml 
```

# Prepare config for wca with static rule-based allocator.
```
kubectl apply -f ./manifests_demo/configmap.yaml
kubectl apply -f ./manifests_demo/pod.yaml
kubectl apply -f ./manifests_demo/pod.yaml --overwrite --force
kubectl create configmap wca-allocator-plugin --from-file example_allocator.py --namespace wca
```

# Show wca
kubectl delete pod wca --namespace wca

kubectl describe pod wca --namespace wca

kubectl get configmap --namespace wca
kubectl get pod --namespace wca

while sleep 1; do kubectl logs -f wca -c wca --namespace wca; done

# Run example workloads manually.

# Run collocation scenario using ansible.

# Cleanup

```
kubectl delete namespaces wca kubecon-demo
```
