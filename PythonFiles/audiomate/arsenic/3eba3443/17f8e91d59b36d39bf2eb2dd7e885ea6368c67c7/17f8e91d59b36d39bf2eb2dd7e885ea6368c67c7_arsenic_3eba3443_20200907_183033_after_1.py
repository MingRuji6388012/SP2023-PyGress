from arsenic.session import Session


class Browser:
    defaults = {}
    session_class = Session

    def __init__(self, **overrides):
        self.capabilities = {**self.defaults, **overrides}


class Firefox(Browser):
    defaults = {"browserName": "firefox", "acceptInsecureCerts": True}


class Chrome(Browser):
    defaults = {"browserName": "chrome"}


class InternetExplorer(Browser):
    session_class = Session
    defaults = {
        "browserName": "internet explorer",
        "version": "",
        "platform": "WINDOWS",
    }


IE = InternetExplorer