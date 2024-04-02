from rich.panel import Panel
from rich.pretty import Pretty
from rich import print


def clog(msg, color="yellow", title=None, subtitle=None):
    print(Panel(Pretty(msg), title=title, subtitle=subtitle, border_style=color))
