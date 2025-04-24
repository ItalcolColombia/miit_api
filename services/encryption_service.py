from cryptography.fernet import Fernet
from utils.process.encryption_process import EncryptionProcess
from core.settings import Settings


SALT = Settings().ENCRYPTION_KEY


class EncryptionService(EncryptionProcess):
    def __init__(self):
        # Load the secret encryption key from environment variables
        self.cipher = Fernet(SALT.encode())

    def encrypt(self, plain_text: str) -> str:
        """Encrypts plain text into an encrypted string."""
        return self.cipher.encrypt(plain_text.encode()).decode()

    def decrypt(self, encrypted_text: str) -> str:
        """Decrypts an encrypted string back to plain text."""
        return self.cipher.decrypt(encrypted_text.encode()).decode()