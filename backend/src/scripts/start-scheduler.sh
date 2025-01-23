#!/bin/bash
set -o errexit
set -o nounset

celery -A askpolis.celery:app beat --loglevel=info
