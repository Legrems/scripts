import sys

import libtmux
from pyfzf.pyfzf import FzfPrompt

# Get active tmux sessions
srv = libtmux.Server()

fzf = FzfPrompt()

mapping = {}
lm = max(len(s.name) for s in srv.sessions if s.name)
for session in srv.sessions:
    string = f"({session.name: <{lm}}) {session.session_path}"
    mapping[string] = session

selections = fzf.prompt(
    ["Select one session you want to switch to"] + list(mapping.keys()),
    "--cycle --header-lines 1 --tmux center",
)

if not selections:
    sys.exit(0)

sess_str = selections[0]
session = mapping[sess_str]
session.switch_client()

session.active_window.active_pane.display_message(
    f"Switched to session: {session.name}"
)
