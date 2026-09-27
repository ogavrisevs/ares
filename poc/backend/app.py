import math
import os
import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from fastapi.staticfiles import StaticFiles


DATABASE_PATH = os.getenv("DATABASE_PATH", "gps.db")


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                recorded_at TEXT NOT NULL
            )
            """
        )


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="GPS Location API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


class LocationCreate(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    recorded_at: datetime | None = None


class Location(LocationCreate):
    id: int
    recorded_at: datetime


def row_to_location(row: sqlite3.Row) -> Location:
    return Location(
        id=row["id"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        recorded_at=datetime.fromisoformat(row["recorded_at"]),
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/locations", response_model=Location, status_code=201)
def create_location(location: LocationCreate) -> Location:
    recorded_at = location.recorded_at or datetime.now(timezone.utc)
    with get_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO locations (latitude, longitude, recorded_at) VALUES (?, ?, ?)",
            (location.latitude, location.longitude, recorded_at.isoformat()),
        )
        row = connection.execute(
            "SELECT id, latitude, longitude, recorded_at FROM locations WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return row_to_location(row)


def distance_meters(a: sqlite3.Row, b: sqlite3.Row) -> float:
    lat1, lon1 = math.radians(a["latitude"]), math.radians(a["longitude"])
    lat2, lon2 = math.radians(b["latitude"]), math.radians(b["longitude"])
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * 6_371_000 * math.asin(math.sqrt(h))


@app.get("/locations", response_model=list[Location])
def list_locations(
    limit: int = Query(default=100, ge=0),
    start: datetime | None = None,
    end: datetime | None = None,
    min_distance: float = Query(default=0, ge=0),
) -> list[Location]:
    """List newest locations first.

    `start`/`end` bound recorded_at (end exclusive). With `min_distance` (meters),
    points closer than that to the previously kept point are skipped, and `limit`
    applies to the points that remain. `limit=0` returns all.
    """
    conditions = []
    params: list[str] = []
    if start is not None:
        conditions.append("julianday(recorded_at) >= julianday(?)")
        params.append(start.isoformat())
    if end is not None:
        conditions.append("julianday(recorded_at) < julianday(?)")
        params.append(end.isoformat())
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    kept: list[sqlite3.Row] = []
    with get_connection() as connection:
        cursor = connection.execute(
            f"""
            SELECT id, latitude, longitude, recorded_at
            FROM locations
            {where}
            ORDER BY recorded_at DESC, id DESC
            """,
            params,
        )
        for row in cursor:
            if min_distance and kept and distance_meters(kept[-1], row) < min_distance:
                continue
            kept.append(row)
            if limit and len(kept) >= limit:
                break
    return [row_to_location(row) for row in kept]


app.mount(
    "/",
    StaticFiles(directory=Path(__file__).resolve().parent.parent / "web", html=True),
    name="web",
)