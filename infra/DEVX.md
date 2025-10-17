# DEVX Stack

This repo contains a local DevX stack to develop and package DSS projects.

## Prerequisites
- Docker + Docker Compose
- mutagen + mutagen-compose
- just (task runner)

## Quick Start
- just setup
- just start
- Open http://localhost:10000 (admin/admin)

## Commands
- just setup  # create DSS, import project and code env
- just start  # start dev with file sync
- just stop   # stop dev (DSS keeps running)
- just build  # export project and code env
- just clean  # remove containers/volumes (export first)

## Workflow

After pulling or rebasing a branch:
- clean setup

Daily:
- start

Before merging:
- clean setup build

