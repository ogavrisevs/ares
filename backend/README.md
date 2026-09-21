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

The map page is available at `http://localhost:8000` and the API is available at `http://localhost:8000`. Interactive API documentation is at `/docs`.

### Allow connections from a remote server

Start Uvicorn on all network interfaces:

```sh
cd backend
.venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
```

On an AWS EC2 server, also allow inbound TCP port `8000` in the instance's security group. For a temporary test, use source `0.0.0.0/0`; restricting it to the frontend server's IP is safer. If UFW is enabled, allow the port too:

```sh
sudo ufw allow 8000/tcp
```

Verify the app locally on the remote server:

```sh
curl http://127.0.0.1:8000/health
ss -ltnp | grep ':8000'
```

### Endpoints

- `GET /health` checks that the service is running.
- `POST /locations` accepts `{ "latitude": 52.52, "longitude": 13.405 }`.
- `GET /locations?limit=100` returns the newest stored coordinates first.

The database is `gps.db` by default. Set `DATABASE_PATH` to use another SQLite file.