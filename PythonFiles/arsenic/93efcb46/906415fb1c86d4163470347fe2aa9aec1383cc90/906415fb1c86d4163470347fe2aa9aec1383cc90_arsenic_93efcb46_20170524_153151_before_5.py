from structlog import get_logger

log = get_logger()


class ArsenicError(Exception):
    pass


class WebdriverError(ArsenicError):
    def __init__(self, message, screen, stacktrace):
        self.message = message
        self.screen = screen
        self.stacktrace = stacktrace
        super().__init__(message)


class UnknownArsenicError(ArsenicError):
    pass


class ArsenicTimeout(ArsenicError):
    pass


CODES = {}


def get(error_code):
    return CODES.get(error_code, UnknownArsenicError)


def create(error_name, *error_codes):
    name = ''.join(bit.capitalize() for bit in error_name.split(' '))
    cls = type(name, (WebdriverError,), {})
    CODES[error_name] = cls
    for code in error_codes:
        CODES[code] = cls
    return cls


NoSuchElement = create('no such element', 7)
NoSuchFrame = create('no such frame', 8)
UnknownCommand = create('unknown command', 9)
StaleElementReference = create('stale element reference', 10)
ElementNotVisible = create('element not visible', 11)
InvalidElementState = create('invalid element state', 12)
UnknownError = create('unknown error', 13)
ElementNotInteractable = create('element not interactable')
ElementIsNotSelectable = create('element is not selectable', 15)
JavascriptError = create('javascript error', 17)
Timeout = create('timeout', 21)
NoSuchWindow = create('no such window', 23)
InvalidCookieDomain = create('invalid cookie domain', 24)
UnableToSetCookie = create('unable to set cookie', 25)
UnexpectedAlertOpen = create('unexpected alert open', 26)
NoSuchAlert = create('no such alert', 27)
ScriptTimeout = create('script timeout', 28)
InvalidElementCoordinates = create('invalid element coordinates', 29)
IMENotAvailable = create('ime not available', 30)
IMEEngineActivationFailed = create('ime engine activation failed', 31)
InvalidSelector = create('invalid selector', 32)
MoveTargetOutOfBounds = create('move target out of bounds', 34)


def _value_or_default(obj, key, default):
    return obj[key] if key in obj else default


def check_response(status, data):
    if status >= 400:
        error = None
        if 'error' in data:
            error = data['error']
        elif 'state' in data:
            error = data['state']

        if 'value' in data:
            data = data['value']
        if error is None and 'error' in data:
            error = data['error']
        message = data.get('message', None)
        stacktrace = data.get('stacktrace', None)
        screen = data.get('screen', None)
        exception_class = get(error)
        log.error('error', type=exception_class, message=message, stacktrace=stacktrace, data=data, status=status)
        raise exception_class(message, screen, stacktrace)
