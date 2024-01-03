# Contributing to aa-charlink

## Setting up the dev environment

### Docker

Docked dev env is very simple to setup. Assuming you have followed the custom image part in the official AA docs, you only need to:

1. Add the following lines in `custom.dockefile`:

    ```dockerfile
    RUN apt-get update && apt-get install make -y
    COPY --chown=${AUTH_USERGROUP} /aa-charlink/charlink/ ./myauth/charlink
    COPY --chown=${AUTH_USERGROUP} /aa-charlink/ /code/charlink
    ```
2. In the `docker-compose.yml` file, add the following lines in the `volumes` section of the `allianceauth` container:

    ```yaml
    - ./aa-charlink/charlink:/home/allianceauth/myauth/charlink
    - ./aa-charlink:/code/charlink
    ```

The above 2 steps will add charlink to the myauth django repository, so the code will be available in the django app without needing to install anything, and will also setup the dev environment to be able to run the tests. You can now run the tests attaching a shell to the container and running `make tox_tests` inside `/code` folder.

### Without Docker

If you don't want to use docker, you can setup the dev environment by following the official AA docs. In order to setup the test environment, you need to either set the following environment variables

- `AA_DB_HOST`: The hostname of the database (for example `localhost`)
- `AA_DB_USER`: The user of the database
- `AA_DB_PASSWORD`: The password of the database user
- `AA_DB_PORT`: The port of the database
- `AA_DB_NAME`: The name of the database

or `USE_MYSQL` to `False`. In the first case the tests will be run against a mysql database, in the second case against a sqlite database. In both cases you also need to set `AA_REDIS` to the host and port of the redis server (for example `localhost:6379`).
