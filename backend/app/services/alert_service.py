import httpx
import structlog

from app.core.config import get_settings

logger = structlog.get_logger()


class AlertService:
    def __init__(self):
        self.settings = get_settings()

    async def send_slack(self, text: str) -> None:
        if not self.settings.slack_webhook_url:
            logger.info("slack_alert_skipped", reason="missing_webhook")
            return
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(self.settings.slack_webhook_url, json={"text": text})

    async def send_telegram(self, chat_id: str, text: str) -> None:
        if not self.settings.telegram_bot_token:
            logger.info("telegram_alert_skipped", reason="missing_token")
            return
        url = f"https://api.telegram.org/bot{self.settings.telegram_bot_token}/sendMessage"
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json={"chat_id": chat_id, "text": text})

    async def send_email(self, to_email: str, subject: str, body: str) -> None:
        logger.info("email_alert_queued", to=to_email, subject=subject, bytes=len(body))
