# Résultats avant/après self-healing

| Test | Avant action | Après action | Preuve |
|---|---:|---:|---|
| Ping h1 -> h2 | ... ms | ... ms | capture terminal |
| Débit iperf h1 -> h2 | ... Mbits/sec | ... Mbits/sec | sortie iperf |
| Chemin réseau | s1-s2 | s1-s3-s2 | dump-flows |
| IP suspecte h3 | accès OK | bloquée | ping h3 -> h2 |
| Wazuh | pas d’alerte | alerte AIOPS_ALERT | dashboard |
| Temps réaction | N/A | ... secondes | timestamp logs |
