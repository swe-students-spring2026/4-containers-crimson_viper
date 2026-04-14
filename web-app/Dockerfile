# use python 3.9 to match pipfile.lock
FROM python:3.9

WORKDIR /app

COPY Pipfile Pipfile.lock ./

# use system so that we don't have a container inside another container
RUN pip install pipenv && pipenv install --deploy
COPY . .
EXPOSE 5000

CMD ["pipenv", "run", "python", "app.py"]