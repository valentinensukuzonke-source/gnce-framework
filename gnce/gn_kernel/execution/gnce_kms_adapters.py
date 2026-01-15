
# GNCE KMS / HSM Adapters (Stubs)
class AWSKMS:
    def sign(self, payload: bytes) -> bytes:
        raise NotImplementedError("Integrate boto3 kms.sign")

class GCPKMS:
    def sign(self, payload: bytes) -> bytes:
        raise NotImplementedError("Integrate google.cloud.kms")

class AzureKeyVault:
    def sign(self, payload: bytes) -> bytes:
        raise NotImplementedError("Integrate azure.keyvault.keys")
