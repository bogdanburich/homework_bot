"""Custom exceptions."""


class UndefinedHomeworkStatus(Exception):
    """Неожиданный статус домашней работы."""

    pass


class FailedToSendMessage(Exception):
    """Не удалось отправить сообщение."""

    pass


class HTTPError(Exception):
    """Код ответа != 200."""

    pass
