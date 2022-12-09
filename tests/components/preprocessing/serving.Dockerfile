FROM python:3.7-slim

LABEL com.amazonaws.sagemaker.capabilities.accept-bind-to-port=true

WORKDIR /app

RUN apt-get update && apt-get install -y gcc
COPY ./requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt \
                                            multi-model-server \
                                            sagemaker-inference

ENV APP_FOLDER="/app"

COPY  src/ $APP_FOLDER/
COPY main.py $APP_FOLDER/

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=$APP_FOLDER
WORKDIR /

ENTRYPOINT ["python", "/app/main.py"]

CMD ["serve"]







