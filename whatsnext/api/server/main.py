from typing import Any, Dict
import uuid
from fastapi import FastAPI, Response, status, HTTPException
from fastapi.params import Body

from pydantic import BaseModel

from . import models

from whatsnext.api.server.database import engine, SessionLocal

models.Base.metadata.create_all(bind=engine)


def get__db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()


def random_string(length: int = 128) -> str:
    return str(uuid.uuid4().hex)[:length]


@app.get("/")
async def root1():
    return {"message": "App 1"}


@app.get("/posts")
async def posts():
    return {"message": "Posts 1 2 and 3"}


class Job(BaseModel):
    id: str = None
    name: str
    project: str
    parameters: Dict[str, Any]


my_jobs = [
    {"id": "1", "name": "job1", "project": "project1", "parameters": {"a": 1, "b": 2}},
    {"id": "2", "name": "job2", "project": "project1", "parameters": {"a": 2, "b": 3}},
    {"id": "3", "name": "job3", "project": "project2", "parameters": {"a": 3, "b": 4}},
]


@app.post("/jobs", status_code=status.HTTP_201_CREATED)
def add_job(
    job: Job,
):
    new_job = job.model_dump()
    new_job["id"] = random_string()
    my_jobs.append(new_job)
    return {"data": new_job}


@app.get("/jobs")
def get_jobs():
    return {"data": my_jobs}


@app.get("/jobs/{id}")
def get_job(id, response: Response):
    for job in my_jobs:
        if job["id"] == id:
            return {"data": job}
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with {id=} not found.")


@app.delete("/jobs/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(id, response: Response):
    for job in my_jobs:
        if job["id"] == id:
            my_jobs.remove(job)
            return
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job with {id=} not found.")
