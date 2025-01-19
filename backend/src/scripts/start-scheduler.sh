#!/bin/bash
set -o errexit
set -o nounset

celery -A askpolis.tasks:app beat --loglevel=info
