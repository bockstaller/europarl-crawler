FROM python:3.9
RUN pip install pipenv
COPY Pipfile* /tmp/
RUN cd /tmp && ls -al && pipenv lock --keep-outdated --requirements > requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY . /tmp
RUN pip install /tmp


WORKDIR /tmp
ENV PYTHONPATH /tmp
CMD ["eurocli", "--help"]