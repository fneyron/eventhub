# QRly

## Appseed
Application is using flask appseed templates. More informations and documentation here : 
https://themesberg.com/docs/flask/volt-dashboard/getting-started/overview/

## Development
In development mode copy the ```.env.template```file to .env and edit with the correct value of your password and API key

## Production - w/ Caprover
We will have to create 4 applications:
- app main application
- app-worker worker for Redis tasks
- app-redis Redis server to manage redis tasks
- app-pgsql postgresql database for data storage



### Postgresql Application (pgsql)
To add the postgresql server: 
1. connect to caprover
2. Click on Apps and One-click apps/database
3. Choose postgresql form the list
4. Set the following parameters:
```
App name: custom
version: latest
username: postgres
password: your_password
default db: postgres
```
Then click on "Deploy"


#### Database Connexion
Find the db id on the caprover server and connect to the database
```
docker ps
docker exec -it d49aa1c52d7e /bin/bash
psql "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}"
```


### Main Application

1. Go to Apps on caprover
2. Check the "Has persistent data" box
3. Create a new app 

In HTTP settings tab: 
- Click on enable https 
- Force Https redirection
- Set the Container HTTP port to 80

In Deployment tab:
- Configure the repository (ie: github.com/fneyron/QRly.git) don't forget to remove the https or ssh
- Enter your private key for deployment from Github
- Add the triggering url to github
- Set captain definition Relative Path to (it will run the "Dockerfile_main" file): 
```
./captain-definition-main
```

In App Config tab:
For the qrly main application the following variables need to be set, it's the same parameters present in .env.template file adapted for production :
```
DEBUG=False
FLASK_APP=run.py
FLASK_ENV=production
DATABASE_URL=postgresql://postgres:password@srv-captain--qrly-db:5432/postgres
REDIS_URL=redis://:password@srv-captain--qrly-redis:6379
ASSETS_ROOT=/static/assets

MAPBOX_TOKEN = 'XXX'
MAIL_USERNAME = "contact@dataik.com"
MAIL_PASSWORD = "XXX"
SECRET_KEY = "XXX"
SECURITY_PASSWORD_SALT = "XXX"

```


# Annexes
## Database migrations
Delete alembic folder : 
```
>>> import sqlite3
>>> conn = sqlite3.connect('apps/db.sqlite3')
>>> cursor = conn.cursor()
>>> cursor.execute('DROP TABLE alembic_version;')
<sqlite3.Cursor object at 0x10052fec0>
>>> conn.close()
```

