import argparse
import configparser
import os
import subprocess
import sys
from pathlib import Path

from pyfzf.pyfzf import FzfPrompt

parser = argparse.ArgumentParser()
parser.add_argument(
    "--no-open",
    action="store_true",
    help="Do not open firefox window. Mostly for debugging",
)
parser_args = parser.parse_args()


BASE_PATH = Path("~/.firefox/").expanduser()

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
selections = fzf.prompt(
    ["Select one or more group to open"] + list(sections.keys()),
    "--cycle --multi --header-lines 1",
)

if not selections:
    sys.exit(0)


for selected_group in selections:
    info = sections[selected_group]
    config = configs[info["config"]]

    prefix = config[info["section"]].get("prefix", "")
    suffix = config[info["section"]].get("suffix", "")

    endpoints = [
        f"{prefix}{e}{suffix}" for e in config[info["section"]]["endpoints"].split("\n")
    ]

    data = ["firefox"]
    for endpoint in endpoints:
        data.extend(["--new-tab", endpoint])

    subprocess.Popen(data)
