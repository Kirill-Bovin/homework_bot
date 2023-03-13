class SendMessageError(Exception):
    """Ошибка при отправке сообщения в telegramm"""
    def __init__(self, message='Сбой при отправке сообщения'):
        self.message = message
        super().__init__(self.message)
