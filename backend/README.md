## GPS backend

Small REST API that receives GPS coordinates and stores them in SQLite.

### Run

```sh
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
```

The API is available at `http://localhost:8000`. Interactive API documentation is at `/docs`.

### Endpoints

- `GET /health` checks that the service is running.
- `POST /locations` accepts `{ "latitude": 52.52, "longitude": 13.405 }`.
- `GET /locations?limit=100` returns the newest stored coordinates first.

The database is `gps.db` by default. Set `DATABASE_PATH` to use another SQLite file.
