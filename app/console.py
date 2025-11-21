from rich.console import Console
from rich.theme import Theme
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from contextlib import contextmanager
import time
import os

# Define Cyberpunk Theme
cyber_theme = Theme({
    "neon_green": "bold #39ff14",
    "neon_pink": "bold #ff00ff",
    "neon_cyan": "bold #00ffff",
    "warning": "bold yellow",
    "error": "bold red",
    "info": "dim cyan",
    "highlight": "bold white on #ff00ff",
    "header": "bold #00ffff on #000000",
})

console = Console(theme=cyber_theme)

def print_cyber_header(title: str, subtitle: str = ""):
    """
    Prints a big, styled header.
    """
    title_text = Text(title, style="neon_green", justify="center")
    if subtitle:
        title_text.append(f"\n{subtitle}", style="neon_pink")

    panel = Panel(
        Align.center(title_text),
        border_style="neon_cyan",
        padding=(1, 2),
        title="[neon_pink]SYSTEM ONLINE[/]",
        subtitle="[neon_pink]v2.0[/]"
    )
    console.print(panel)

def print_cyber_panel(content, title: str = None, border_style="neon_cyan"):
    """
    Prints content inside a cyberpunk styled panel.
    """
    console.print(
        Panel(
            content,
            title=f"[neon_green]{title}[/]" if title else None,
            border_style=border_style,
            padding=(1, 2)
        )
    )

def print_step(text: str, style="info"):
    """
    Prints a step with a typing effect (simulated by just printing for now to avoid slowing down too much,
    but we could add delays).
    """
    console.print(f"[{style}]>> {text}[/{style}]")

def cyber_input(prompt_text: str, password: bool = False) -> str:
    """
    Styled input prompt.
    """
    return Prompt.ask(f"[neon_green]{prompt_text}[/neon_green]", password=password)

@contextmanager
def loading_animation(description: str = "Processing..."):
    """
    Context manager for a loading spinner.
    """
    with Progress(
        SpinnerColumn(style="neon_pink"),
        TextColumn("[bold cyan]{task.description}"),
        transient=True,
        console=console
    ) as progress:
        progress.add_task(description, total=None)
        yield

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_ascii_art():
    art = r"""
 [neon_cyan]
      .                                                      .
        .n                   .                 .                  n.
  .   .dP                  dP                   9b                 9b.    .
 4    qXb         .       dX                     Xb       .        dXp     t
dX.    9Xb      .dXb    __                     __    dXb.     dXP     .Xb
9XXb._       _.dXXXXb dXXXXbo.               .odXXXXb dXXXXb._       _.dXXP
 9XXXXXXXXXXXXXXXXXXXVXXXXXXXXOo.           .oOXXXXXXXXVXXXXXXXXXXXXXXXXXXXP
  `9XXXXXXXXXXXXXXXXXXXXX'~   ~`OOO8b   d8OOO'~   ~`XXXXXXXXXXXXXXXXXXXXXP'
    `9XXXXXXXXXXXP' `9XX'   DIE    `98v8P'  HUMAN   `XXP' `9XXXXXXXXXXXP'
        ~~~~~~~       9X.          .db|db.          .XP       ~~~~~~~
                        )b.  .dbo.dP'`v'`9b.odb.  .dX(
                      ,dXXXXXXXXXXXb     dXXXXXXXXXXXb.
                     dXXXXXXXXXXXP'   .   `9XXXXXXXXXXXb
                    dXXXXXXXXXXXXb   d|b   dXXXXXXXXXXXXb
                    9XXb'   `XXXXXb.dX|Xb.dXXXXX'   `dXXP
                     `'      9XXXXXX(   )XXXXXXP      `'
                              XXXX X.`v'.X XXXX
                              XP^X'`b   d'`X^XX
                              X. 9  `   '  P )X
                              `b  `       '  d'
                               `             '
 [/neon_cyan]
[bold neon_pink]
 _  _                      _        ___
| || |___ __ ___ _____ _ _| |_  _  |   \ ___ _ __  ___ _ _  ___
| __ / -_) _` \ V / -_) ' \ | || | | |) / -_) '  \/ _ \ ' \(_-<
|_||_\___|\__,_|\_/\___|_||_|_|\_, | |___/\___|_|_|_\___/_||_/__/
                               |__/
[/bold neon_pink]
    """
    console.print(Align.center(art))
