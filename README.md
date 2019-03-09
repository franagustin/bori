# Bot Oficial de la República de Insomniac
Python-based discord bot. Now in discord.py rewrite version.

---

## Installation
* Install python 3.7
* Install discord.py
* git clone https://github.com/francokuchiki/bori-ghost-rewrite/
* Install postgresql (sudo pacman -S postgresql | sudo apt-get install postgresql)
* Run `sudo -u postgres initdb -D /var/lib/postgres/data`
* Run `sudo systemctl start postgresql`
* Run `psql -U postgres`
* Write `CREATE USER ghost WITH PASSWORD 'password';`
* Write `CREATE DATABASE ghost WITH OWNER ghost;`
* Write `\q`
