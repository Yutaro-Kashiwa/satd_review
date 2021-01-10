kubectl create secret generic smbcreds --from-literal username=posl --from-literal password="dosukoi@Honda"
kubectl apply -f pv.yml
kubectl create -f https://raw.githubusercontent.com/kubernetes-csi/csi-driver-smb/master/deploy/example/pvc-smb-static.yaml
