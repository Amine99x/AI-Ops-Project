#!/usr/bin/env python3
import os
import subprocess
import time

def run(cmd):
    print(f"\n[controller] {cmd}")
    subprocess.run(cmd, shell=True)

def main():
    print("=== AIOps Self-Healing Controller Helper ===")
    print("Ce script prépare les fichiers et vérifie les dépendances.")
    print("La topologie Mininet doit rester lancée dans un terminal séparé.")

    os.makedirs("evidence/screenshots", exist_ok=True)

    run("sudo touch /var/log/network.log")
    run("sudo chmod 666 /var/log/network.log")
    run("ansible all -m ping")
    run("sudo ovs-vsctl show")
    run("sudo ovs-ofctl dump-flows s1 || true")

    print("\nÉtapes recommandées pour la démo :")
    print("1. Terminal 1 : sudo python3 topology.py")
    print("2. Terminal 2 : sudo python3 metrics.py")
    print("3. Terminal 3 : sudo python3 ai_detection.py")
    print("4. Dans Mininet : h2 iperf -s &")
    print("5. Dans Mininet : h1 iperf -c 10.0.0.2 -t 120 -i 1")
    print("6. Dans Mininet : h3 ping -f 10.0.0.2 ou h3 nmap 10.0.0.0/24")
    print("7. Montrer Wazuh + flows + CSV + logs.")

if __name__ == "__main__":
    main()
