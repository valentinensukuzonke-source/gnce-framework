
# GNCE Cryptographic Key Management & Signing
import hashlib, hmac, os, json
from datetime import datetime, timezone

class GNCEKeyStore:
    def __init__(self, secret: bytes | None = None):
        self.secret = secret or os.urandom(32)

    def sign(self, payload: dict) -> str:
        blob = json.dumps(payload, sort_keys=True).encode()
        return hmac.new(self.secret, blob, hashlib.sha256).hexdigest()

    def verify(self, payload: dict, signature: str) -> bool:
        return hmac.compare_digest(self.sign(payload), signature)

def sign_cet(cet: dict, keystore: GNCEKeyStore) -> dict:
    cet = dict(cet)
    cet["signed_at"] = datetime.now(timezone.utc).isoformat()
    cet["signature"] = keystore.sign(cet)
    return cet
