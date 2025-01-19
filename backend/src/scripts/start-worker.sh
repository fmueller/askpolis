#!/bin/bash
set -o errexit
set -o nounset

celery -A askpolis.celery:app worker --loglevel=info --concurrency=1
