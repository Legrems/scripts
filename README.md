# Scripts

## tmux-sessionizer
Inspired by [ThePrimeagen](https://github.com/ThePrimeagen/.dotfiles/blob/master/bin/.local/scripts/tmux-sessionizer), but in python

Create/load tmux session based on the path of a project, use fzf for selection

## tmux-ssh-group
Open multiple ssh connection to multiple servers as sudo, can pass extra commands also.
Will open a new window in tiled mode on all this servers at the same times

Read from config files located under `~/.ssh-tmux/`, with the format:
```
[Gestion controller]
servers = myserver1.fqdn
          myserver2.fqdn
          myserver3.fqdn
          myserver4.fqdn
commands = ls -l
```
