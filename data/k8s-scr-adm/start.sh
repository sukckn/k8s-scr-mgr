#!/bin/bash
cd /k8s-scr-adm
exec gunicorn -b :5000 --access-logfile - --error-logfile - k8s-scr-adm:app

