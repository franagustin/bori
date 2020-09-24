FROM python:3.8-slim-buster

# Install any dependencies needed

# Must update first or packages won't be found
RUN apt-get update 

# Install one package per command to avoid reinstalling every
# package when modifying a single line.
# -y flag prevents prompting for confirmation and consequently failing.
RUN apt-get install -y --no-install-recommends git

COPY ./requirements.txt /requirements/
RUN pip install -r /requirements/requirements.txt
RUN rm -r /requirements

COPY ./ /src

WORKDIR /src
