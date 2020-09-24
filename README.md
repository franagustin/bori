# Bot Oficial de la República de Insomniac
Python-based discord bot. Now in discord.py rewrite version.

---

## Dependencies
* Python 3.8 (*should run with 3.7 too*).
* Docker
* Docker-Compose

## Installing
* Download this repository: `git clone https://github.com/francokuchiki/bori`.
* Create **.env** file copying .env.example: `cp .env.example .env`.
* Change settings inside **.env** file as you see fit.
* Start Mongo's and Redis's docker containers (or use your own): `docker-compose up -d mongo redis`.
* Start the bot's docker container: `docker-compose up bot`
