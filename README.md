# DB Diary

[![lint-free](https://github.com/swe-students-spring2026/4-containers-crimson_viper/actions/workflows/lint.yml/badge.svg)](https://github.com/swe-students-spring2026/4-containers-crimson_viper/actions/workflows/lint.yml)
[![log github events](https://github.com/swe-students-spring2026/4-containers-crimson_viper/actions/workflows/event-logger.yml/badge.svg)](https://github.com/swe-students-spring2026/4-containers-crimson_viper/actions/workflows/event-logger.yml)
## Project Description

This project is a containerized journaling application built with three connected subsystems: a Flask web app, a machine learning client, and a MongoDB database.

The web app allows users to create an account, sign in, and use the journaling interface. Users can record audio reflections, and the machine learning client processes those audio files by transcribing the speech and analyzing the emotional tone. The database stores user data, audio job records, and machine learning results so that the web app and machine learning client can use the same shared data.

This repository is organized as a monorepo. The `web-app` directory contains the Flask application. The `machine-learning-client` directory contains the machine learning subsystem. MongoDB runs in its own container through Docker Compose.

## Team Members

## Project Structure

## How to Configure and Run the Project

Before running the project, make sure the following are installed on your machine:

- Docker
- Docker Compose

You can check this with:

```bash
docker --version
docker compose version

```

From the root of the repository, run:

```bash
docker compose build
docker compose up

```
Then open this URL in your browser: `http://127.0.0.1:5001/`

After creating an account and signing in, you can start exploring the main features of the app, including writing journal entries, recording audio reflections, and viewing your daily entries.
