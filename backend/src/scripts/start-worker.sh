#!/bin/bash
set -o errexit
set -o nounset

celery -A tasks.app worker --loglevel=info --concurrency=1
