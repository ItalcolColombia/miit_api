from abc import ABC, abstractmethod

class Email(ABC):
    @abstractmethod
    def send_email(self, recipient_email: str, subject_email: str, body_email: str) -> None:
        """
        Sends an email to the specified recipient.

        This abstract method defines the interface for sending emails in concrete implementations.
        It should handle the composition and delivery of an email with the provided recipient,
        subject, and body.

        Args:
            recipient_email (str): The email address of the recipient.
            subject_email (str): The subject line of the email.
            body_email (str): The body content of the email.

        Returns:
            None: This method does not return a value.

        Raises:
            BasedException: For unexpected errors during the email sending process, such as
                SMTP connection failures, authentication errors, or invalid recipient addresses.
        """
        pass