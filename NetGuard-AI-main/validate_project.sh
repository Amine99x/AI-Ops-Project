#!/bin/bash
echo "===== AIOps Project Validation ====="

echo "[1] Dossier projet"
pwd
tree -a -L 2

echo "[2] Versions"
python3 --version
ansible --version | head -n 2
docker --version
docker-compose --version
ovs-vsctl --version | head -n 2

echo "[3] Services"
sudo systemctl status openvswitch-switch --no-pager | head -n 10
sudo systemctl status docker --no-pager | head -n 10

echo "[4] Docker containers"
sudo docker ps

echo "[5] OVS status"
sudo ovs-vsctl show

echo "[6] OVS flows"
sudo ovs-ofctl dump-flows s1 || true
sudo ovs-ofctl dump-flows s2 || true
sudo ovs-ofctl dump-flows s3 || true

echo "[7] Logs AIOps"
tail -n 20 /var/log/network.log || true

echo "[8] Metrics CSV"
tail -n 10 evidence/metrics.csv || true

echo "===== Validation finished ====="

