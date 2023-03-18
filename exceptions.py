class KirillTeleBotError(Exception):
    pass


class HTTPError(KirillTeleBotError):
    pass


class HttpResponseNotOkError(KirillTeleBotError):
    pass


class WrongKeyHw(KirillTeleBotError):
    pass
