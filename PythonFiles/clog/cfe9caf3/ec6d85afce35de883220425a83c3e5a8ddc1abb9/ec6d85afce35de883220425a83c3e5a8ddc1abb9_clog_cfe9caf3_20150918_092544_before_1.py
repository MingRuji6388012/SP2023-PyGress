from pprint import pformat
from django.utils.termcolors import colorize


def clog(msg, color="yellow", title=None):
    if title:
        print(colorize("------- {0} ---------".format(title), fg=color))
    print(colorize(pformat(msg), fg=color))
