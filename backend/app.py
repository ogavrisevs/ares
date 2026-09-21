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


@app.get("/locations", response_model=list[Location])
def list_locations(limit: int = Query(default=100, ge=1, le=1000)) -> list[Location]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, latitude, longitude, recorded_at
            FROM locations
            ORDER BY recorded_at DESC, id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [row_to_location(row) for row in rows]


app.mount(
    "/",
    StaticFiles(directory=Path(__file__).resolve().parent.parent / "web", html=True),
    name="web",
)