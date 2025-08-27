#!/bin/bash
cd /pull-scr
exec gunicorn -b :5000 --access-logfile - --error-logfile - pull-scr:app

