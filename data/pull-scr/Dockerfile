FROM python:3.14-rc-slim

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt 
RUN pip install gunicorn

COPY pull-scr pull-scr
COPY start.sh pull-scr/
RUN chmod a+x /pull-scr/start.sh

RUN apt-get update -y && apt-get install -y curl

RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
RUN install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

EXPOSE 5000
ENTRYPOINT ["/pull-scr/start.sh"]