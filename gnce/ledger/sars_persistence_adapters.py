
# GNCE SARS Persistence Adapters
# Supports hash-chain ledger and DLT stub

import hashlib, json
from datetime import datetime, timezone

class HashChainLedger:
    def __init__(self):
        self.chain = []
        self.prev_hash = "GENESIS"

    def append(self, artifact: dict) -> dict:
        blob = json.dumps(artifact, sort_keys=True).encode()
        h = hashlib.sha256(self.prev_hash.encode() + blob).hexdigest()
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "artifact": artifact,
            "prev_hash": self.prev_hash,
            "hash": h,
        }
        self.chain.append(record)
        self.prev_hash = h
        return record

class DLTStub:
    def commit(self, record: dict) -> str:
        # Placeholder for blockchain / DLT integration
        return f"DLT_TX_{hash(record['hash'])}"
