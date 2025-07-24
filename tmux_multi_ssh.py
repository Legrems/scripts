import argparse
import configparser
import sys
import time
from pathlib import Path

import libtmux
from pyfzf.pyfzf import FzfPrompt

parser = argparse.ArgumentParser()
parser.add_argument("--servers-file", "-f", help="Servers file to connect to")
parser_args = parser.parse_args()

if parser_args.servers_file:
    with open(parser_args.servers_file, "r") as file:
        data = file.read()

    servers = []
    for line in data.strip().split("\n"):
        servers.append(line.strip())

config = configparser.ConfigParser()
config_path = Path("~/.ssh-tmux-multi.ini").expanduser()
config.read(config_path)

fav_key = "Favourite servers"
fzf = FzfPrompt()


def get_all_known_ssh_hosts():
    servers = set()

    # Check known hosts on ssh folder
    with open(Path("~/.ssh/known_hosts").expanduser(), "r") as file:
        lines = file.read().strip().split("\n")

    for line in lines:
        servers.add(line.split(" ")[0])

    # Check previous ssh command on histfile
    with open(
        Path("~/.histfile").expanduser(), "r", encoding="utf-8", errors="ignore"
    ) as file:
        lines = file.read().strip().split("\n")

    for line in lines:
        if line[15:].startswith("ssh "):
            server = line[19:].strip()
            if server:
                servers.add(server)

    return sorted(list(servers), reverse=True)


def get_favourite_servers_first():
    servers = get_all_known_ssh_hosts()

    if fav_key not in config.sections():
        return servers

    order = {}
    for server in servers:
        order[server] = "0"

    for server, uses in config[fav_key].items():
        if server in order:
            order[server] = uses

    # Return the most used servers first
    for count, value in order.items():
        print(count, value)
    return [x[0] for x in sorted(order.items(), key=lambda x: x[1], reverse=True)]


def write_choosen_servers(servers):
    """Write the servers usage in the config file."""

    if fav_key not in config.sections():
        config[fav_key] = {}

    for server in servers:
        if server in config[fav_key]:
            config[fav_key][server] = str(int(config[fav_key][server]) + 1)

        else:
            config[fav_key][server] = "1"

    with open(config_path, "w") as file:
        config.write(file)


if not parser_args.servers_file:
    servers = fzf.prompt(
        ["Select server to connect to"] + get_favourite_servers_first(),
        "--cycle --multi --print-query --header-lines 1 --tmux center",
    )

# Strip from query if found else, use the query
if len(servers) > 1:
    servers = servers[1:]

if not servers:
    sys.exit(1)

write_choosen_servers(servers)

srv = libtmux.Server()
active_session = srv.sessions.filter(session_attached="1")[0]
window = active_session.new_window(
    f"ssh-multis {','.join(servers)}", window_shell=f"ssh {servers[0]}"
)

for server in servers[1:]:
    window.select_layout("tiled")
    pane = window.split(shell=f"ssh {server}")

# Wait until tmux finished working
time.sleep(0.1)

# Confirm connection on asking panes
confirmation_needed_text = (
    "Are you sure you want to continue connecting (yes/no/[fingerprint])?"
)
for pane in window.panes:
    pane_content = pane.capture_pane()
    if pane_content and confirmation_needed_text == pane_content[-1]:
        pane.send_keys("yes")

window.set_window_option("synchronize-panes", "on")
pane = window.panes[0]
pane.send_keys("sudo su -")
window.set_window_option("synchronize-panes", "off")

window.select()
