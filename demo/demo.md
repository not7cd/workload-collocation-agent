wd owca
cd demo
export PS1='%{$fg_bold[grey]%}# %{$reset_color%}'
clear


# Clean state
kubectl delete namespace wca
kubectl delete namespace workloads

kubectl get configmaps -n wca 
kubectl get secrets -n wca 
kubectl get all -n wca 
kubectl get all -n workloads 

clear

# ENABLE 1 config
# ENABLE LOGS
# DISABLE OTHER SCeNARIONS
# COMMIT





# ########################################
# Part 1 - installation and basic features
# ########################################




# Kubernetes setups
kubectl get nodes -owide



# Create "wca" namespace and secret
kubectl create namespace wca
kubectl create -n wca secret generic kubelet-key-crt --from-file=kubelet-client.crt --from-file=kubelet-client.key


# Deploy "wca" pod
kubectl apply -f wca.yaml



# Check status
kubectl -n wca get pod wca
kubectl -n wca describe pod wca



# Watch WCA logs (window on the right)
while sleep 1; do kubectl logs -n wca -f wca -c wca; done



# Check that metrics are exported properly.
clear
kubectl exec -n wca wca -c wca -- cat /var/lib/wca/anomalies.prom
curl -s 100.64.176.34:9100/metrics | grep wca_tasks



# Deploy simple synthetic workload "stress".
clear
kubectl create namespace workloads
kubectl create -f stress1.yaml
kubectl get pods 




# Edit "stress1" pod labels to reclassify pod as "best-effort".
kubectl edit pod stress1




# Show that low level CPU/RDT resources are properly configured.
clear
ssh 100.64.176.34 'head /sys/fs/cgroup/cpu/kubepods/besteffort/*/cpu.cfs_quota_us'
ssh 100.64.176.34 'ls -1 /sys/fs/resctrl/'
ssh 100.64.176.34 'cat /sys/fs/resctrl/best-effort/schemata'
ssh 100.64.176.34 'head /sys/fs/resctrl/best-effort/mon_groups/*/mon_data/mon_L3_00/*'


# Edit configuration e.g. enable more resource for best-effort tasks.
kubectl -n wca edit configmap wca-config


# Check Low level CPU/RDT resources are properly reconfigured.
clear
ssh 100.64.176.34 'head /sys/fs/cgroup/cpu/kubepods/besteffort/*/cpu.cfs_quota_us'
ssh 100.64.176.34 'ls -1 /sys/fs/resctrl/'
ssh 100.64.176.34 'cat /sys/fs/resctrl/best-effort/schemata'
ssh 100.64.176.34 'head /sys/fs/resctrl/best-effort/mon_groups/*/mon_data/mon_L3_00/*'

# Run another similar pod already classifed as "latency-critical".
kubectl create -f stress2.yaml
kubectl get pods 

# Check Low level CPU/RDT resources are properly reconfigured for another pod.
clear
ssh 100.64.176.34 'head /sys/fs/cgroup/cpu/kubepods/burstable/*/cpu.cfs_quota_us'
ssh 100.64.176.34 'ls -1 /sys/fs/resctrl/'
ssh 100.64.176.34 'cat /sys/fs/resctrl/latency-critical/schemata'
ssh 100.64.176.34 'head /sys/fs/resctrl/latency-critical/mon_groups/*/mon_data/mon_L3_00/*'

# If resgroup name is not specified it would get default based on pod name.
# Edit the rules first to remove "name" for RDTAllocation.
kubectl -n wca edit configmap wca-config
clear

# Each pods get now own resctrl group.
ssh 100.64.176.34 'ls -1 /sys/fs/resctrl/'



### Replace static allocator with "hello world" (and change to log level to info).
# Recreate WCA pod with new configuration.
vi wca.yaml
kubectl delete pod wca --namespace wca ; kubectl apply -f wca.yaml

# Let's see that new metrics is exposed.
curl -s 100.64.176.34:9100/metrics | grep hello_world




# Show metrics collected by WCA in Prometheus http://100.64.176.12:9090.




# ########################################################
# Part 2 - working example of allocator for real workload
# ########################################################


# Delete existing pods.
kubectl delete pods --all
kubectl get pods




# Deploy WCA allocator python-based plugin as configmap.
vi example_allocator.py
kubectl delete configmap wca-allocator-plugin -n wca ; kubectl create configmap wca-allocator-plugin --from-file example_allocator.py -n wca




# Reconfigure WCA to use python based plugin (third configuration)
vi wca.yaml
# Redeploy wca with new config.
kubectl delete pod wca --namespace wca ; kubectl apply -f wca.yaml





# Run real workload (memcached fork with mutilate as load generator)
kubectl create namespace workloads
vi scenario1.yaml
ansible-playbook -i scenario1.yaml ../workloads/run_workloads.yaml --tags twemcache_mutilate
kubectl get pods 









# Details of latency-critical pod
kubectl get pod 34--twemcache-mutilate-default--twemcache--11311-0 -ojson | jq .





# Latency-critical workload - load generator
eubectl get pod 34--twemcache-mutilate-default--mutilate--11311-0 -ojson | jq .




# Observer performance characteristic of latency-critical workload running alone.
# in Grafana
http://100.64.176.12:3000 





# Run best-effort task causing the interference.
ansible-playbook -i scenario1.yaml ../workloads/run_workloads.yaml --tags stress_ng
kubectl get pods




# Observe impact of best-effort on IPC metric and application performance (Grafana)
http://100.64.176.12:3000/d/L0bI_XmWk/kubecon-demo-2019





# Reclassify stress-ng as best-effort to enable WCA control over "best-effort" task.
kubectl edit pod 34--stress-ng-default--0



# The negative effect of running "best-effort" job should disappear.
http://100.64.176.12:3000/d/L0bI_XmWk/kubecon-demo-2019



# Delete the aggressor and observe that performance goes back to normal
kubectl delete pod 34--stress-ng-default--0




# ################################################
# THE END
# ################################################

