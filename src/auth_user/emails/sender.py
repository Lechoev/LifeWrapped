import smtplib
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.conf.logger import get_logger

logger = get_logger(__name__)


class EmailSenderInterface(ABC):
    @abstractmethod
    def send_verification_code(self, email: str, code: str) -> None: ...


class SmtpEmailSender(EmailSenderInterface):
    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        from_email: str,
        use_tls: bool = True,
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.from_email = from_email
        self.use_tls = use_tls

    def _create_message(self, to_email: str, subject: str, body: str) -> MIMEMultipart:
        msg = MIMEMultipart("alternative")
        msg["From"] = self.from_email
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        return msg

    def send_verification_code(self, email: str, code: str) -> None:
        subject = "Код подтверждения"
        body = f"Ваш код подтверждения: {code}"

        msg = self._create_message(email, subject, body)

        try:
            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()

                server.login(self.user, self.password)
                server.send_message(msg)

        except smtplib.SMTPException:
            logger.exception(
                "Failed to send verification email", extra={"email": email}
            )
            raise
