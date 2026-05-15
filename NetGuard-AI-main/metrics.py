#!/usr/bin/env python3
import csv
import os
import re
import subprocess
import time
from datetime import datetime

CSV_FILE = "evidence/metrics.csv"
SWITCH = "s1"
INTERVAL = 2


def run_cmd(cmd):
    return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.STDOUT)


def parse_dump_ports(output):
    rx_bytes = 0
    tx_bytes = 0
    rx_dropped = 0
    tx_dropped = 0
    rx_errors = 0
    tx_errors = 0

    for line in output.splitlines():
        line = line.strip()

        m_rx = re.search(r"rx pkts=.*?bytes=(\d+).*?drop=(\d+).*?err(?:s|ors)?=(\d+)", line)
        if m_rx:
            rx_bytes += int(m_rx.group(1))
            rx_dropped += int(m_rx.group(2))
            rx_errors += int(m_rx.group(3))

        m_tx = re.search(r"tx pkts=.*?bytes=(\d+).*?drop=(\d+).*?err(?:s|ors)?=(\d+)", line)
        if m_tx:
            tx_bytes += int(m_tx.group(1))
            tx_dropped += int(m_tx.group(2))
            tx_errors += int(m_tx.group(3))

    return {
        "rx_bytes": rx_bytes,
        "tx_bytes": tx_bytes,
        "rx_dropped": rx_dropped,
        "tx_dropped": tx_dropped,
        "rx_errors": rx_errors,
        "tx_errors": tx_errors,
    }


def ensure_csv():
    os.makedirs("evidence", exist_ok=True)
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp",
                "rx_bytes",
                "tx_bytes",
                "rx_dropped",
                "tx_dropped",
                "rx_errors",
                "tx_errors",
                "mbps",
                "drop_delta",
                "error_delta",
            ])


def main():
    ensure_csv()
    previous = None
    previous_time = None

    print("[metrics] Collecte OVS demarree. CTRL+C pour arreter.")

    while True:
        try:
            output = run_cmd(f"sudo ovs-ofctl dump-ports {SWITCH}")
            current = parse_dump_ports(output)
            now = time.time()

            if previous is None:
                mbps = 0.0
                drop_delta = 0
                error_delta = 0
            else:
                elapsed = max(now - previous_time, 0.001)
                byte_delta = (
                    current["rx_bytes"] + current["tx_bytes"]
                    - previous["rx_bytes"] - previous["tx_bytes"]
                )
                mbps = (byte_delta * 8) / elapsed / 1_000_000

                drop_delta = (
                    current["rx_dropped"] + current["tx_dropped"]
                    - previous["rx_dropped"] - previous["tx_dropped"]
                )

                error_delta = (
                    current["rx_errors"] + current["tx_errors"]
                    - previous["rx_errors"] - previous["tx_errors"]
                )

            row = [
                datetime.now().isoformat(timespec="seconds"),
                current["rx_bytes"],
                current["tx_bytes"],
                current["rx_dropped"],
                current["tx_dropped"],
                current["rx_errors"],
                current["tx_errors"],
                round(mbps, 3),
                drop_delta,
                error_delta,
            ]

            with open(CSV_FILE, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(row)

            print(f"[metrics] mbps={mbps:.3f} drop_delta={drop_delta} error_delta={error_delta}")

            previous = current
            previous_time = now
            time.sleep(INTERVAL)

        except subprocess.CalledProcessError as e:
            print("[metrics] Erreur commande OVS:", e.output)
            time.sleep(INTERVAL)
        except KeyboardInterrupt:
            print("\n[metrics] Arret.")
            break


if __name__ == "__main__":
    main()
