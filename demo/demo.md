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
kubectl delete pod wca --namespace wca
kubectl apply -f wca.yaml

kubectl delete pod wca --namespace wca ; kubectl apply -f wca.yaml

kubectl create secret generic kubelet-key-crt --from-file=kubelet-client.crt --from-file=kubelet-client.key --namespace=wca

# Backup
kubectl delete pod wca --namespace wca
kubectl describe pod wca --namespace wca
kubectl get configmap wca-config --namespace wca
kubectl get pod wca -o wide --namespace wca

## Deploy WCA allocator python-based plugin as configmap
kubectl delete configmap wca-allocator-plugin --namespace wca ; kubectl create configmap wca-allocator-plugin --from-file example_allocator.py --namespace wca

kubectl get configmap wca-allocator-plugin --namespace wca


## WCA pod logs
while sleep 1; do kubectl logs -f wca -c wca --namespace wca; done


###  RESTROT ALL
kubectl delete configmap wca-allocator-plugin --namespace wca ; kubectl create configmap wca-allocator-plugin --from-file example_allocator.py --namespace wca
kubectl delete pod wca --namespace wca ; kubectl apply -f wca.yaml


# #############################
# Simple          workloads
# #############################

# Run example workloads manually.
kubectl create namespace workloads
kubectl config set-context --current --namespace workloads
kubectl create -f stress-ng1.yaml
kubectl create -f stress-ng2-lc.yaml
kubectl get pods
kubectl get pods stress-ng1
kubectl get pods stress-ng2

kubectl delete -f stress-n1.yaml
kubectl delete -f stress-n2.yaml

### Run collocation scenario using ansible.

### Cleanup
kubectl delete namespaces wca kubecon-demo
```

ansible-playbook -i scenario1.yaml ../workloads/run_workloads.yaml --tags clean_jobs
ansible-playbook -i scenario1.yaml ../workloads/run_workloads.yaml --tags stress_ng
ansible-playbook -i scenario1.yaml ../workloads/run_workloads.yaml --tags twemcache_mutilate

