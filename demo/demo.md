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





# #########################################
# Part 1 - installation and basic features
# #########################################




# Kubernetes setup.
kubectl get nodes -owide



# Create "wca" namespace and secret with key to access kubelet.
kubectl create namespace wca
kubectl create -n wca secret generic kubelet-key-crt --from-file=kubelet-client.crt --from-file=kubelet-client.key
ls -1



# Deploy "wca" pod.
vi wca.yaml
clear
kubectl apply -f wca.yaml




# Check status.
kubectl -n wca get pod wca
kubectl -n wca describe pod wca



# Watch WCA logs (window on the right).
while sleep 1; do kubectl logs -n wca -f wca -c wca; done



# Check that metrics are exported properly.
clear
kubectl exec -n wca wca -c wca -- cat /var/lib/wca/anomalies.prom
clear
curl -s 100.64.176.34:9100/metrics | grep wca_tasks



# Deploy simple synthetic workload "stress".
clear
kubectl create namespace workloads
kubectl config set-context --current --namespace workloads
kubectl get pods 
vi stress1.yaml
clear
kubectl create -f stress1.yaml
kubectl get pods 




# Edit "stress1" pod labels to reclassify pod as "best-effort".
kubectl edit pod stress1
clear




# Show that low level CPU/RDT resources are properly configured.
clear
ssh 100.64.176.34 'head /sys/fs/cgroup/cpu/kubepods/besteffort/*/cpu.cfs_quota_us'
clear
ssh 100.64.176.34 'ls -1 /sys/fs/resctrl/'
clear
ssh 100.64.176.34 'cat /sys/fs/resctrl/best-effort/schemata'

# ... and RDT monitoring is properly configured.
clear
ssh 100.64.176.34 'head /sys/fs/resctrl/best-effort/mon_groups/*/mon_data/mon_L3_00/*'
clear



# Edit configuration e.g. enable more resource for best-effort tasks.
kubectl -n wca edit configmap wca-config



# Check low-level CPU/RDT resources are properly reconfigured.
clear
ssh 100.64.176.34 'head /sys/fs/cgroup/cpu/kubepods/besteffort/*/cpu.cfs_quota_us'
clear
ssh 100.64.176.34 'cat /sys/fs/resctrl/best-effort/schemata'




# Run another similar pod already classifed as "latency-critical".
clear
kubectl create -f stress2.yaml
kubectl get pods 




# Check Low level CPU/RDT resources are properly reconfigured for another pod.
clear
ssh 100.64.176.34 'head /sys/fs/cgroup/cpu/kubepods/burstable/*/cpu.cfs_quota_us'
clear
ssh 100.64.176.34 'ls -1 /sys/fs/resctrl/'
clear
ssh 100.64.176.34 'cat /sys/fs/resctrl/latency-critical/schemata'




# If resgroup name is not specified it would get default based on pod name.
# Edit the rules first to remove "name" for RDTAllocation.
kubectl -n wca edit configmap wca-config
clear




# Each pods get now own resctrl group.
ssh 100.64.176.34 'ls -1 /sys/fs/resctrl/'



### Replace static allocator with "hello world" (and change to log level to info).
# Recreate WCA pod with new configuration.
vi wca.yaml
clear
kubectl delete pod wca --namespace wca ; kubectl apply -f wca.yaml



# Let's see that new metric is exposed by node_exporter.
curl -s 100.64.176.34:9100/metrics | grep hello_world
clear




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
vi scenario1.yaml
clear
ansible-playbook -i scenario1.yaml ../workloads/run_workloads.yaml --tags twemcache_mutilate
kubectl get pods 




# Details of latency-critical pod
kubectl get pod 34--twemcache-mutilate-default--twemcache--11311-0 -ojson | jq .




# Latency-critical workload - load generator
kubectl get pod 34--twemcache-mutilate-default--mutilate--11311-0 -ojson | jq .




# Observer performance characteristic of latency-critical workload running alone.
# in Grafana
http://100.64.176.12:3000 





# Run best-effort task causing the interference (without label for now).
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



# ################################################
# Platform Resource Manager toolkit integration
# ################################################

cd ../..
git clone https://github.com/intel/platform-resource-manager
cd platform-resource-manager
git submodule update --init
cd prm
make package
cd ../../../serenity/owca/demo
cp ../../platform-resource-manager/prm/dist/prm-plugin.pex .

kubectl delete configmap prm-plugin -n wca ; kubectl create configmap prm-plugin --from-file prm-plugin.pex -n wca

cat prm/Dockerfile
docker build -t 100.64.176.12:80/wca-prm -f prm/Dockerfile prm/
docker push 100.64.176.12:80/wca-prm:latest


# Reconfigure (4.)

kubectl delete configmap prm-plugin -n wca ; kubectl create -n wca configmap prm-plugin --from-file prm/workload.json

kubectl delete pod wca --namespace wca ; kubectl apply -f wca.yaml
