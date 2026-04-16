FROM python:3.9

WORKDIR /app
COPY  Pipfile Pipfile.lock ./

# we need this for whisper
RUN apt-get update && apt-get install -y ffmpeg

# use system so that we don't have a container inside another container
RUN pip install pipenv && pipenv install --system

COPY . .

CMD ["python", "main.py"]