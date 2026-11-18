import logging

import httpx

logger = logging.getLogger(__name__)


class AntiFraudeClient:
    """Avisa o gateway anti-fraude (fictício) sobre cada transferência."""

    def __init__(self, url: str | None = None):
        self._url = url

    def notificar(self, evento: dict) -> None:
        if not self._url:
            return
        try:
            httpx.post(self._url, json=evento, timeout=2.0)
        except httpx.HTTPError:
            logger.warning("Falha ao notificar o anti-fraude")