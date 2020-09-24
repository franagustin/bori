# Bot Oficial de la República de Insomniac
Python-based discord bot. Now in discord.py rewrite version.

---

## Dependencies
### With Docker
* Docker
* Docker-Compose

### Without Docker
* Python 3.8 (*should run with 3.7 too*).
* MongoDB
* Redis


## Installing
* Download this repository: `git clone https://github.com/francokuchiki/bori`.
* Create **.env** file copying .env.example: `cp .env.example .env`.
* Change settings inside **.env** file as you see fit.

### With Docker
* Start Mongo's and Redis's docker containers (or use your own): `docker-compose up -d mongo redis`.
* Start the bot's docker container: `docker-compose up bot`


### Without Docker
* You will need both a MongoDB instance and a Redis instance running.
* Be sure to correctly set your MongoDB and Redis host and credentials on **.env**!
* Start the bot by running the **main.py** file: `python main.py`.
