#!/bin/bash
set -o errexit
set -o nounset

alembic upgrade head

celery -A tasks.app worker --loglevel=info --concurrency=1
