#!/bin/bash
set -o errexit
set -o nounset

celery -A tasks.app beat --loglevel=info
