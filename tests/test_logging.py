import json
import logging

import pytest

from logging_config import configure_logging, log_context


def test_logs_mask_correlation_ids_and_omit_secrets(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging("INFO")
    logger = logging.getLogger("test")

    with log_context(
        thread_id="12345678-1234-1234-1234-123456789abc",
        run_id="abcdef12-1234-1234-1234-abcdef123456",
    ):
        logger.info("safe_event", extra={"backend": "memory"})

    payload = json.loads(capsys.readouterr().out)
    serialized = json.dumps(payload)
    assert payload["thread_id"] == "1234...9abc"
    assert payload["run_id"] == "abcd...3456"
    assert payload["event"] == "safe_event"
    assert "GOOGLE_API_KEY" not in serialized
