from unittest.mock import Mock, patch

import pytest

from src.auth_user.tasks import send_email


def test_send_email_task_success():
    mock_cache = Mock()
    mock_sender = Mock()
    mock_service = Mock()

    mock_cache.set_if_not_exists = Mock(return_value=True)
    mock_service.send = Mock(return_value=True)

    with (
        patch("src.auth_user.tasks.get_redis_cache", return_value=mock_cache),
        patch("src.auth_user.tasks.get_email_sender", return_value=mock_sender),
        patch(
            "src.auth_user.tasks.VerificationEmailService", return_value=mock_service
        ),
    ):
        result = send_email("test@example.com", "123456")

        mock_service.send.assert_called_once_with("test@example.com", "123456")
        assert result is None


def test_send_email_task_rate_limited():
    mock_cache = Mock()
    mock_sender = Mock()
    mock_service = Mock()

    mock_cache.set_if_not_exists = Mock(return_value=False)
    mock_service.send = Mock(return_value=False)

    with (
        patch("src.auth_user.tasks.get_redis_cache", return_value=mock_cache),
        patch("src.auth_user.tasks.get_email_sender", return_value=mock_sender),
        patch(
            "src.auth_user.tasks.VerificationEmailService", return_value=mock_service
        ),
    ):
        result = send_email("test@example.com", "123456")

        assert result is None
        mock_service.send.assert_called_once_with("test@example.com", "123456")


def test_send_email_task_exception():
    mock_cache = Mock()
    mock_sender = Mock()
    mock_service = Mock()

    mock_service.send = Mock(side_effect=Exception("SMTP error"))

    with (
        patch("src.auth_user.tasks.get_redis_cache", return_value=mock_cache),
        patch("src.auth_user.tasks.get_email_sender", return_value=mock_sender),
        patch(
            "src.auth_user.tasks.VerificationEmailService", return_value=mock_service
        ),
    ):
        with pytest.raises(Exception, match="SMTP error"):
            send_email("test@example.com", "123456")


def test_send_email_task_with_real_mocks():
    mock_cache = Mock()
    mock_sender = Mock()

    with (
        patch("src.auth_user.tasks.get_redis_cache", return_value=mock_cache),
        patch("src.auth_user.tasks.get_email_sender", return_value=mock_sender),
    ):
        mock_cache.set_if_not_exists = Mock(return_value=True)
        mock_sender.send_verification_code = Mock()

        result = send_email("test@example.com", "123456")

        assert result is None
        mock_cache.set_if_not_exists.assert_called_once_with(
            key="verification:test@example.com", value="locked", ttl=60
        )
        mock_sender.send_verification_code.assert_called_once_with(
            "test@example.com", "123456"
        )
