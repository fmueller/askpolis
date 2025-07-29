# Backend

Tha backend of AskPolis. It contains the main application: the API, analytical backend and scraping of the data.

## Development with Docker

The Dockerfile supports a development mode used by `compose.yaml`. When the
environment variable `ASKPOLIS_DEV` is set to `true`, the container reloads the
`src` folder on changes.

Start the stack with:

```bash
docker compose up --build
```
