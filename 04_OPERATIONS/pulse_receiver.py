from __future__ import annotations

import json
import sys
from realtime_organism import CoupledOrganism

organism = CoupledOrganism()

print("Pulse receiver active. Send JSON lines like:")
print('{"timestamp": 1712345678.12, "bpm": 78.0, "source": "apple_watch"}')
print()

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue

    try:
        data = json.loads(line)
        log = organism.ingest_bpm(
            timestamp=float(data["timestamp"]),
            bpm=float(data["bpm"]),
            source=str(data.get("source", "unknown")),
        )
        print(
            json.dumps(
                {
                    "timestamp": log.timestamp,
                    "bpm": log.bpm,
                    "signal": round(log.signal, 4),
                    "activity": round(log.activity, 4),
                    "coherence": round(log.coherence, 4),
                    "resources": round(log.resources, 4),
                    "state": log.state.value,
                }
            )
        )
    except Exception as e:
        print(json.dumps({"error": str(e), "raw": line}))
