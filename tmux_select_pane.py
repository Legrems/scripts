import argparse
import sys
from collections import defaultdict
from pprint import pprint

import libtmux
import sh
from pyfzf.pyfzf import FzfPrompt

parser = argparse.ArgumentParser()
parser.add_argument(
    "--no-open",
    action="store_true",
    help="Do not open tmux window. Mostly for debugging",
)
parser_args = parser.parse_args()


# Get active tmux sessions
srv = libtmux.Server()

fzf = FzfPrompt()
commands = defaultdict(list)

all_tty = [p.pane_tty for p in srv.panes]

cmd = f"-t {' -t '.join(all_tty)} -o pid:10 -o tty:10 -o command -ww"  # -f

sh_commands = sh.ps(cmd.split(" ")).stdout.decode().strip().split("\n")

# Ignore first lines (i.e: table headers)
for cmd in sh_commands[1:]:
    pid = cmd[:10].strip()
    tty = cmd[10:20].strip()
    command = cmd[20:].strip()
    tty_number = int(tty.replace("pts/", ""))

    if command in ["-zsh", "/bin/zsh"]:
        continue

    commands[tty_number].append(
        {
            "pid": int(pid),
            "command": command,
        }
    )


def format_pane(pane):
    global commands

    tty_number = int(pane.pane_tty.replace("/dev/pts/", ""))
    running_commands = sorted(commands[tty_number], key=lambda c: c["pid"])

    if len(running_commands) >= 1:
        cmd = running_commands[0]

    else:
        cmd = {"pid": "-", "command": "*command not found*"}

    path = pane.pane_current_path.replace("/home/legrems/Documents/Arcanite", "~/D/A")
    path = path.replace("/home/legrems/Documents", "~/D")
    path = path.replace("/home/legrems", "~")
    return [
        f"{pane.pane_tty}: [{pane.session_name}: {pane.window_name}, {path}]: {cmd['command']}"
    ]


panes = []
for pane in srv.panes:
    panes.extend(format_pane(pane))
selections = fzf.prompt(
    ["Select one pane you want to switch to"] + panes,
    "--cycle --header-lines 1 --tmux center",
)

if not selections:
    sys.exit(0)

pane_name = selections[0]
tty = pane_name.split(":")[0]

selected_pane = srv.panes.get(pane_tty=tty)

if parser_args.no_open:
    print(selected_pane)
    print(tty)
    tty_number = int(tty.replace("/dev/pts/", ""))
    pprint(commands[tty_number])

else:
    # Go to this session
    selected_pane.session.switch_client()

    # Select the correct window
    selected_pane.window.select()

    # And switch to this pane
    selected_pane.window.select_pane(selected_pane.pane_id)
