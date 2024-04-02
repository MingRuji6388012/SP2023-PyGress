from pprint import pformat
from . import colors


def colorize(color, text):
    f = getattr(colors, color)
    return f(text)


def clog(msg, color="yellow", title=None):
    if title:
        print(colorize(color, "------- {0} ---------".format(title)))
    print(colorize(color, pformat(msg)))


def test():
    for c in ['red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white']:
        print(colorize(c, "Hello World!"))
