import libtmux
import sys


from pyfzf.pyfzf import FzfPrompt

# Get active tmux sessions
srv = libtmux.Server()

fzf = FzfPrompt()
selections = fzf.prompt(["Select one session you want to switch to"] + [s.name for s in srv.sessions], "--cycle --header-lines 1")

if not selections:
    sys.exit(0)

session_name = selections[0]

session = srv.sessions.filter(name=session_name)[0]
session.switch_client()
session.active_window.active_pane.display_message(f"Switched to session: {session_name}")
