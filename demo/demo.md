# 0. Cleanup
kubectl delete namespace wca
kubectl delete namespace workloads
kubectl get all --namespace wca 
kubectl get cm --namespace wca 
kubectl get all --namespace workloads 

# #############################
# Workload Collocation Agent
# #############################

# 1. Install Workload Collocation Agent on cluster
### Prepare namespace
kubectl create namespace wca

## Deploy WCA pod with static allocator configuration
kubectl apply -f wca.yaml
kubectl apply -f wca.yaml --overwrite --force

# backup
kubectl delete pod wca --namespace wca
kubectl describe pod wca --namespace wca
kubectl get configmap wca-config --namespace wca
kubectl get pod wca -o wide --namespace wca

## Deploy WCA allocator python-based plugin as configmap
kubectl create configmap wca-allocator-plugin --from-file example_allocator.py --namespace wca
kubectl delete configmap wca-allocator-plugin --namespace wca

## WCA pod logs
while sleep 1; do kubectl logs -f wca -c wca --namespace wca; done


# Show wca state


# #############################
#           Workloads
# #############################

# Run example workloads manually.
kubectl create namespace workloads
kubectl config set-context --current --namespace workloads
kubectl create -f stress-ng1.yaml
kubectl get pods stress-ng1
kubectl get pods stress-ng2

kubectl delete -f stress-n1.yaml
kubectl delete -f stress-n2.yaml

### Run collocation scenario using ansible.

### Cleanup
kubectl delete namespaces wca kubecon-demo
```
