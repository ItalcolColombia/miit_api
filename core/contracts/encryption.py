from abc import ABC, abstractmethod

class Encryption(ABC):
    @abstractmethod
    def encrypt(self, plain_text: str) -> str:
        """
        Encrypts a plain text string and returns the encrypted value.

        Args:
            plain_text (str): The plain text to encrypt.

        Returns:
            str: The encrypted text as a string.

        Raises:
            BasedException: For unexpected errors during the encryption process.
        """
        pass

    @abstractmethod
    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypts an encrypted string and returns the plain text value.

        Args:
            encrypted_text (str): The encrypted text to decrypt.

        Returns:
            str: The decrypted plain text.

        Raises:
            BasedException: For unexpected errors during the decryption process.
        """
        pass