FROM python:3.9-slim-buster

WORKDIR /dspback

COPY requirements.txt requirements.txt

COPY dspback .

RUN pip install -r requirements.txt

EXPOSE 5002

ENV PYTHONPATH "${PYTHONPATH}:/dspback/dspback"

CMD ["python", "dspback/main.py"]
