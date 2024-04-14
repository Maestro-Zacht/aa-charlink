ARG AA_DOCKER_TAG
FROM $AA_DOCKER_TAG

USER root
RUN apt-get update && apt-get install make -y
USER ${AUTH_USER}

RUN cd /home/allianceauth
COPY .devcontainer/requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . /workspace
RUN ln -s /workspace/charlink myauth/charlink

RUN allianceauth update myauth