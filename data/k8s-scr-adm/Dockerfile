FROM python:3.14-rc-slim

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt 
RUN pip install gunicorn

COPY k8s-scr-adm k8s-scr-adm
COPY start.sh k8s-scr-adm/
RUN chmod a+x /k8s-scr-adm/start.sh

RUN mkdir -p /k8s-scr-adm/yaml
RUN chmod 777 /k8s-scr-adm/yaml

RUN apt-get update -y && apt-get install -y curl

RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
RUN install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl

EXPOSE 5000
ENTRYPOINT ["/k8s-scr-adm/start.sh"]
#ENTRYPOINT ["/bin/bash"]