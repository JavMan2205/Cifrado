import secrets
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes

class CryptoManager:
    def __init__(self, key_size=2048):
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=key_size
        )
        self.public_key = self.private_key.public_key()

    def cifrar_texto(self, texto_plano):
        return self.public_key.encrypt(
            texto_plano.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

    def descifrar_texto(self, texto_cifrado):
        try:
            decrypted = self.private_key.decrypt(
                texto_cifrado,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            return decrypted.decode()
        except Exception:
            return None

def generar_token_unico():
    return secrets.token_urlsafe(16)[:12]