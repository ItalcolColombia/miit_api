import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from starlette import status

from core.contracts.email import Email
from core.exceptions.base_exception import BasedException
from utils.logger_util import LoggerUtil

log = LoggerUtil()

class EmailService(Email):
    def __init__(self, smtp_host: str, smtp_port: int, smtp_user: str, smtp_password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password

    def send_email(self, recipient_email: str, subject_email: str, body_email: str) -> None:
        """
        Send email to the specified recipient.

        Args:
            recipient_email (str): The recipient's email address.
            subject_email (str): The subject of the email.
            body_email (str): The body content of the email.

        Raises:
            BasedException: For unexpected errors during the email sending process.
        """
        try:
            # Compose the email message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user  # From is your Gmail address
            msg['To'] = recipient_email  # To is the recipient's address
            msg['Subject'] = subject_email

            body = body_email
            msg.attach(MIMEText(body, 'plain'))

            log.info("Intentando enviar email...")
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                log.info("SMTP server connection successful.")
                server.starttls()  # Make sure TLS is used
                server.login(self.smtp_user, self.smtp_password)
                text = msg.as_string()
                server.sendmail(self.smtp_user, recipient_email, text)
                log.info(f'Confirmation email sent to {recipient_email}')
        except Exception as e:
            log.error(f"Failed to send email: {str(e)}")
            raise BasedException(
                message="Error inesperado al enviar el correo.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )