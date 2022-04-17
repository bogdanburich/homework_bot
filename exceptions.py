"""Custom exceptions."""


class UndefinedHomeworkStatus(Exception):
    """Неожиданный статус домашней работы."""

    pass


class FailedToSendMessage(Exception):
    """Не удалось отправить сообщение."""

    pass
