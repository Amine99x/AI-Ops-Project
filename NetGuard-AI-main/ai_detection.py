#!/usr/bin/env python3
import csv
import os
import subprocess
import time
from datetime import datetime

import numpy as np
from sklearn.ensemble import IsolationForest

CSV_FILE = "evidence/metrics.csv"
LOG_FILE = "/var/log/network.log"

TRAIN_SAMPLES = 12
CHECK_INTERVAL = 3
COOLDOWN_SECONDS = 25
DRY_RUN = False

MBPS_THRESHOLD = 8.0
DROP_THRESHOLD = 1
ERROR_THRESHOLD = 1

PLAYBOOK_QOS = "qos.yml"
PLAYBOOK_REROUTE = "reroute.yml"
PLAYBOOK_ACL = "acl_block.yml"

last_action_time = 0


def log_event(message):
    line = f"{datetime.now().isoformat(timespec='seconds')} {message}"
    print(line)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except PermissionError:
        print("[ai] Permission denied writing log. Run with sudo.")


def run_playbook(playbook):
    if DRY_RUN:
        log_event(f"SELF_HEALING_ACTION playbook={playbook} status=dry_run")
        return
    cmd = f"ansible-playbook {playbook}"
    log_event(f"SELF_HEALING_ACTION playbook={playbook} status=started")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            log_event(f"SELF_HEALING_ACTION playbook={playbook} status=success")
        else:
            err = result.stderr.strip().replace("\n", " ")
            log_event(f"SELF_HEALING_ACTION playbook={playbook} status=failed error='{err[:120]}'")
    except Exception as e:
        log_event(f"SELF_HEALING_ACTION playbook={playbook} status=exception error='{e}'")


def read_metrics():
    if not os.path.exists(CSV_FILE):
        return []
    rows = []
    with open(CSV_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rows.append([
                    float(row["mbps"]),
                    float(row["drop_delta"]),
                    float(row["error_delta"]),
                ])
            except Exception:
                continue
    return rows


def main():
    global last_action_time

    log_event("AIOPS_INFO controller=ai_detection status=started")
    model = None

    while True:
        rows = read_metrics()

        if len(rows) < TRAIN_SAMPLES:
            print(f"[ai] Waiting for baseline data: {len(rows)}/{TRAIN_SAMPLES}")
            time.sleep(CHECK_INTERVAL)
            continue

        data = np.array(rows)

        if model is None:
            model = IsolationForest(contamination=0.15, random_state=42)
            model.fit(data[:TRAIN_SAMPLES])
            log_event("AIOPS_INFO model=IsolationForest status=trained")
            time.sleep(CHECK_INTERVAL)
            continue

        current = data[-1].reshape(1, -1)
        mbps = current[0][0]
        drop_delta = current[0][1]
        error_delta = current[0][2]

        prediction = model.predict(current)[0]
        anomaly_by_model = prediction == -1
        anomaly_by_threshold = (
            mbps > MBPS_THRESHOLD
            or drop_delta >= DROP_THRESHOLD
            or error_delta >= ERROR_THRESHOLD
        )

        print(f"[ai] mbps={mbps:.3f} drops={drop_delta} errors={error_delta} model={prediction}")

        if anomaly_by_model or anomaly_by_threshold:
            now = time.time()
            if now - last_action_time < COOLDOWN_SECONDS:
                print("[ai] Anomaly detected, cooldown active.")
                time.sleep(CHECK_INTERVAL)
                continue

            last_action_time = now
            log_event(
                f"AIOPS_ALERT type=network_anomaly mbps={mbps:.3f} "
                f"drops={drop_delta} errors={error_delta} model_prediction={prediction}"
            )

            run_playbook(PLAYBOOK_QOS)
            run_playbook(PLAYBOOK_REROUTE)

            if mbps > (MBPS_THRESHOLD * 1.5) or drop_delta > 3 or error_delta > 0:
                log_event(
                    f"ATTACK_DETECTED suspected_ip=10.0.0.3 "
                    f"reason=high_traffic_or_drops mbps={mbps:.3f}"
                )
                run_playbook(PLAYBOOK_ACL)

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
