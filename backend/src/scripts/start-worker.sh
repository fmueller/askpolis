#!/bin/bash
set -o errexit
set -o nounset

celery -A askpolis.tasks:app worker --loglevel=info --concurrency=1
