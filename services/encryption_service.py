from cryptography.fernet import Fernet, InvalidToken
from starlette import status

from core.exceptions.base_exception import BasedException
from core.config.settings import get_settings
from utils.logger_util import LoggerUtil

SALT = get_settings().ENCRYPTION_KEY
log = LoggerUtil()


class EncryptionService:
    def __init__(self):
        self.cipher = Fernet(SALT.encode())

    def encrypt(self, plain_text: str) -> str:
        """
        Encrypts plain text into an encrypted string.

        Args:
            plain_text (str): The plain text to encrypt.

        Returns:
            str: The encrypted text as a string.

        Raises:
            BasedException: For unexpected errors during the encryption process.
        """
        try:
            return self.cipher.encrypt(plain_text.encode()).decode()
        except Exception as e:
            log.error(f"Error al encriptar el texto: {e}")
            raise BasedException(
                message="Error al encriptar el texto.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypts an encrypted string back to plain text.

        Args:
            encrypted_text (str): The encrypted text to decrypt.

        Returns:
            str: The decrypted plain text.

        Raises:
            InvalidToken: If the encrypted text is invalid or cannot be decrypted.
            BasedException: For other unexpected errors during the decryption process.
        """
        try:
            return self.cipher.decrypt(encrypted_text.encode()).decode()
        except InvalidToken as e:
            log.error(f"Error al desencriptar: Token inválido - {e}")
            raise
        except Exception as e:
            log.error(f"Error al desencriptar el texto: {e}")
            raise BasedException(
                message="Error inesperado al desencriptar el texto.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
