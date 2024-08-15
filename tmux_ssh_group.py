import libtmux
import configparser
import argparse
import time
import sys
import os


from pathlib import Path
from pyfzf.pyfzf import FzfPrompt


parser = argparse.ArgumentParser()
parser.add_argument("--no-open", action="store_true", help="Do not open tmux window. Mostly for debugging")
parser.add_argument("--separate-sessions", "-s", action="store_true", help="Use a separate sessions for all of the groups")
parser_args = parser.parse_args()


def get_window_name(session_name):
    name = session_name.replace("-", "").replace("  ", " ").replace(" ", "_")
    return f"{'' if parser_args.separate_sessions else 'ssh-multig '}{name}"

BASE_PATH = Path("~/.ssh-tmux/").expanduser()

configs = {}
sections = {}
for subconffile in os.listdir(BASE_PATH):
    if not subconffile.endswith(".ini"):
        continue

    prefix = subconffile.replace(".ini", "").capitalize()
    config = configparser.ConfigParser()
    config.read(BASE_PATH / subconffile)

    configs[subconffile] = config

    for section in config.sections():
        section_name = f"[{prefix}] {section}"
        sections[section_name] = {
            "section": section,
            "config": subconffile,
        }

fzf = FzfPrompt()
selections = fzf.prompt(["Select one or more servers group to open"] + list(sections.keys()), "--cycle --multi --header-lines 1")

if not selections:
    sys.exit(0)

# Get active tmux sessions
srv = libtmux.Server()
active_sessions = srv.attached_sessions

if parser_args.separate_sessions:
    sessions = srv.sessions.filter(name="SSH-MultiG")

    if sessions:
        active_session = sessions[0]

    else:
        active_session = srv.new_session(session_name="SSH-MultiG")

else:
    if len(active_sessions) > 1:
        session_choice = fzf.prompt(["You have multiple active tmux sessions open. Choose one to create the window on"] + [sess.name for sess in active_sessions], "--cycle --header-lines 1")

        if not session_choice:
            sys.exit(0)

        active_session = srv.sessions.filter(name=session_choice[0])[0]

    elif len(active_sessions) == 1:
        active_session = active_sessions[0]

    else:
        raw_try = srv.cmd("display", "-p", "#{session_name}").stdout
        if raw_try:
            active_session = srv.sessions.filter(name=raw_try[0])[0]

        else:
            active_session = srv.sessions[0]

for selected_group in selections:

    info = sections[selected_group]
    config = configs[info["config"]]
    servers = config[info["section"]]["servers"].split("\n")

    extra_commands = []
    if "commands" in config[info["section"]].keys():
        extra_commands = config[info["section"]]["commands"].split("\n")

    if parser_args.no_open:
        print(selected_group)
        print(f" - Servers ({len(servers)}):")
        for server in servers:
            print(f"    * {server}")

        if extra_commands:
            print(f"  - Extra commands ({len(extra_commands)}):")
            for command in extra_commands:
                print(f"    * {command}")

        continue

    if not servers:
        continue

    window_name = get_window_name(selected_group)
    if windows := active_session.windows.filter(name=window_name):
        windows[0].select()
        continue

    window = active_session.new_window(window_name, window_shell=f"ssh {servers[0]}")

    for server in servers[1:]:
        pane = window.split(shell=f"ssh {server}")
        # Select tiled layout each time, to ensure enough space
        window.select_layout("tiled")

    # Wait until tmux finished working
    time.sleep(0.05)

    # Confirm connection on asking panes
    confirmation_needed_text = "Are you sure you want to continue connecting (yes/no/[fingerprint])?"
    for pane in window.panes:
        pane_content = pane.capture_pane()
        if pane_content and confirmation_needed_text == pane_content[-1]:
            pane.send_keys("yes")

    window.set_window_option("synchronize-panes", "on")
    pane = window.panes[0]
    pane.send_keys("sudo su -")

    for command in extra_commands:
        pane.send_keys(command)

    window.set_window_option("synchronize-panes", "off")
    window.select()
    window.select_layout("tiled")

active_session.switch_client()
