export PS0='%{$fg_bold[grey]%}# %{$reset_color%}'
clear

# Clean state
kubectl delete namespace wca
kubectl delete namespace workloads

kubectl get configmaps -n wca 
kubectl get secrets -n wca 
kubectl get all -n wca 
kubectl get all -n workloads 


# #############################
# Part 1 - features
# #############################

# WCA Namespace and secret
kubectl create namespace wca
kubectl create -n wca secret generic kubelet-key-crt --from-file=kubelet-client.crt --from-file=kubelet-client.key


# Deploy pod
kubectl apply -f wca.yaml



# Check status
kubectl -n wca get pod wca
kubectl -n wca describe pod wca



# Watch WCA logs
while sleep 1; do kubectl logs -n wca -f wca -c wca; done



# Check that metrics are saved/exported properly.
clear
kubectl exec -n wca wca -c wca -- cat /var/lib/wca/anomalies.prom
curl -s 100.64.176.33:9100/metrics | grep wca_tasks



# Deploy simple synthetic workload "stress"
clear
kubectl create namespace workloads
kubectl create -f stress1.yaml
kubectl get pods 

# Low level CPU/RDT resources are properly configured

clear
ssh 100.64.176.33 'head /sys/fs/cgroup/cpu/kubepods/besteffort/*/cpu.cfs_quota_us'
ssh 100.64.176.33 'ls -1 /sys/fs/resctrl/'
ssh 100.64.176.33 'cat /sys/fs/resctrl/best-effort/schemata'
ssh 100.64.176.33 'head /sys/fs/resctrl/best-effort/mon_groups/*/mon_data/mon_L3_00/*'


# Edit Pod labels to reclassify pod as best-effort.
kubectl edit pod stress1



# Edit configuration e.g. enable more resource for best-effort tasks.
kubectl -n wca edit configmap wca-config



# Run another similar pod and classify it as latency-critical.
kubectl create -f stress2.yaml
kubectl get pods 


### Replace static allocator with "hello world".

# Recreate WCA pod with new configuration.
vi wca.yaml
kubectl delete pod wca --namespace wca ; kubectl apply -f wca.yaml
curl -s 100.64.176.33:9100/metrics | grep hello_world
open http://100.64.176.12:9090

# ###################################
# Part 2 - working example
# ###################################
# Recreate WCA pod with new configuration to use "no-op allocator"
vi wca.yaml
kubectl delete pod wca --namespace wca ; kubectl apply -f wca.yaml

# Delete existing pods and run scenario1
kubectl delete pods --all

# Run real workload (memcache fork with mutilate load generator)
ansible-playbook -i scenario1.yaml ../workloads/run_workloads.yaml --tags clean_jobs
kubectl get pods

ansible-playbook -i scenario1.yaml ../workloads/run_workloads.yaml --tags twemcache_mutilate
kubectl get pods

# Run best-effort tasks causing the interference and how WCA deals with it)
ansible-playbook -i scenario1.yaml ../workloads/run_workloads.yaml --tags stress_ng
kubectl get pods

# Latency-critical pod
kubectl get pod 33--twemcache-mutilate-default--twemcache--11311-0 -ojson | jq .

# Latency-critical workload - load generator
kubectl get pod 33--twemcache-mutilate-default--mutilate--11311-0 -ojson | jq .

# Observer impact of best-effort on cache misses ration and application performance (Prometheus/Grafana)
http://100.64.176.12:9090 

# Delete the aggressor obeserve that performance goes back to normal
kubectl delete pod 33--stress-ng-default--0

# Open Prometheus/Grafana
http://100.64.176.12:3000/d/L0bI_XmWk/kubecon-demo-2019


# Deploy WCA allocator python-based plugin as configmap
vi example_allocator.py
kubectl delete configmap wca-allocator-plugin -n wca ; kubectl create configmap wca-allocator-plugin --from-file example_allocator.py -n wca

# Reconfigure WCA to use python based plugin (3. scenario)
vi wca.yaml
kubectl delete pod wca --namespace wca ; kubectl apply -f wca.yaml


