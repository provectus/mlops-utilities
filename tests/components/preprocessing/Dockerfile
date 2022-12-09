FROM python:3.7-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt \
                                            multi-model-server \
                                            sagemaker-inference

COPY ./src /app/src
COPY main.py /app/

ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "main.py"]
