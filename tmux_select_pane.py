import libtmux
import sys
import sh
from collections import defaultdict


from pyfzf.pyfzf import FzfPrompt

# Get active tmux sessions
srv = libtmux.Server()

fzf = FzfPrompt()
commands = defaultdict(list)

all_tty = [p.pane_tty for p in srv.panes]

cmd = f"-t {' -t '.join(all_tty)} -o pid:10 -o tty:10 -o command -ww"

sh_commands = sh.ps(cmd.split(' ')).stdout.decode().strip().split("\n")

# Ignore first lines (i.e: table headers)
for cmd in sh_commands[1:]:
    pid = cmd[:10].strip()
    tty = cmd[10:20].strip()
    command = cmd[20:].strip()
    tty_number = int(tty.replace("pts/", ""))

    commands[tty_number].append(
        {
            "pid": pid,
            "command": command,
        }
    )


def format_pane(pane):
    global commands

    tty_number = int(pane.pane_tty.replace("/dev/pts/", ""))
    running_commands = commands[tty_number]

    if len(running_commands) == 2:
        cmd = running_commands[-1]

    else:
        cmd = {"pid": "-", "command": "-"}

    return f"{pane.pane_tty}: [Sess:{pane.session_name}, Win:{pane.window_name}] (cwd:{pane.pane_current_path}): {cmd['command']}"


panes = [format_pane(pane) for pane in srv.panes]
selections = fzf.prompt(["Select one pane you want to switch to"] + panes, "--cycle --header-lines 1")

if not selections:
    sys.exit(0)

pane_name = selections[0]
tty = pane_name.split(":")[0]

selected_pane = srv.panes.get(pane_tty=tty)

# Go to this session
selected_pane.session.switch_client()

# Select the correct window
selected_pane.window.select()

# And switch to this pane
selected_pane.window.select_pane(selected_pane.pane_id)
