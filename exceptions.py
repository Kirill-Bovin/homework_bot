class GetAPIException(Exception):
    """Исключение для проблем доступа к API."""

    pass


class UnavailableAPIException(GetAPIException):
    """Исключение для неправильного кода доступа к API."""

    pass


def err_msg(error):
    """Генерация сообщения об ошибке."""
    return f'Сбой в работе программы: {error}'
