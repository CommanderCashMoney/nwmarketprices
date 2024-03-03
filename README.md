<div align="center" id="top"> 
  <img src="./nwmarketapp/static/nwmarketapp/android-chrome-192x192.png" alt="Nwmarketprices" />

  &#xa0;

  <!-- <a href="https://nwmarketprices.netlify.app">Demo</a> -->
</div>

<h1 align="center">Nwmarketprices</h1>

<p align="center">
  <img alt="Github top language" src="https://img.shields.io/github/languages/top/CommanderCashMoney/nwmarketprices?color=56BEB8">

  <img alt="Github language count" src="https://img.shields.io/github/languages/count/CommanderCashMoney/nwmarketprices?color=56BEB8">

  <img alt="Repository size" src="https://img.shields.io/github/repo-size/CommanderCashMoney/nwmarketprices?color=56BEB8">

  <img alt="License" src="https://img.shields.io/github/license/CommanderCashMoney/nwmarketprices?color=56BEB8">

  <!-- <img alt="Github issues" src="https://img.shields.io/github/issues/CommanderCashMoney/nwmarketprices?color=56BEB8" /> -->

  <!-- <img alt="Github forks" src="https://img.shields.io/github/forks/CommanderCashMoney/nwmarketprices?color=56BEB8" /> -->

  <!-- <img alt="Github stars" src="https://img.shields.io/github/stars/CommanderCashMoney/nwmarketprices?color=56BEB8" /> -->
</p>

<!-- Status -->

<!-- <h4 align="center"> 
	🚧  Nwmarketprices 🚀 Under construction...  🚧
</h4> 

<hr> -->

<p align="center">
  <a href="#dart-about">About</a> &#xa0; | &#xa0; 
  <a href="#sparkles-features">Features</a> &#xa0; | &#xa0;
  <a href="#rocket-technologies">Technologies</a> &#xa0; | &#xa0;
  <a href="#white_check_mark-requirements">Requirements</a> &#xa0; | &#xa0;
  <a href="#checkered_flag-starting">Starting</a> &#xa0; | &#xa0;
  <a href="#memo-license">License</a> &#xa0; | &#xa0;
  <a href="https://github.com/CommanderCashMoney" target="_blank">Author</a>
</p>

<br>

## :dart: About ##

Display specified server prices of New World

## :sparkles: Features ##

:heavy_check_mark: Items search;\
:heavy_check_mark: 15 days rolling price chart;\
:heavy_check_mark: Popular end game items;\
:heavy_check_mark: Popular base materials;\
:heavy_check_mark: Competitive items;\
:heavy_check_mark: Motes;\
:heavy_check_mark: Refining reagents;\
:heavy_check_mark: Trophy materials;\

## :rocket: Technologies ##

The following tools were used in this project:

- [Python](https://www.python.org/)
- [Django](https://www.djangoproject.com/)
- [Postgresql](https://www.postgresql.org/)
- [Javascript](https://www.javascript.com/)

## :white_check_mark: Requirements ##

Before starting :checkered_flag:, you need to have [Git](https://git-scm.com) and [Python](https://www.python.org/) installed.

## :checkered_flag: Starting ##

```bash
# Clone this project
$ git clone https://github.com/CommanderCashMoney/nwmarketprices

# Access
$ cd nwmarketprices

# Install dependencies
$ pip3 install -r requirements

# Run the project
$ python3 ./manage.py runserver

# The server will initialize in the <http://localhost:8080>
```

## :checkered_flag: Database with Docker ##

```bash
# Get your dump
$ wget https://scraperdownload.s3.us-west-1.amazonaws.com/full-prodAWS_PROD2-2023_04_10_08_02_36-dump.sql

# Lauch database
$ docker-compose up

# Connect to the database
$ docker exec -i postgres psql -U postgres

# Create a database named nwmp_prod (CREATE DATABASE nwmp_prod) then exit
# Populate the new database
$ cat ./full-prodAWS_PROD2-2023_04_10_08_02_36-dump.sql | docker exec -i postgres psql -U postgres -d nwmp_prod

# You can access adminer at <http://localhost:8000>
```

## :checkered_flag: .env file example ##

```bash
DB_NAME=nwmp_prod
RDS_USERNAME=postgres
RDS_PASSWORD=postgres
RDS_HOSTNAME=localhost
RDS_PORT=5432
DEBUG=True
```

## :memo: License ##



Made with :heart: by <a href="https://github.com/CommanderCashMoney" target="_blank">CommanderCashMoney</a>

&#xa0;

<a href="#top">Back to top</a>
