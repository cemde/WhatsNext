from fastapi import Depends, FastAPI, Response
from sqlalchemy.orm import Session

from . import models
from .database import engine, get_db
from .routers import jobs, projects, tasks

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(jobs.router)
app.include_router(projects.router)
app.include_router(tasks.router)


@app.get("/checkdb")
def check_db(db: Session = Depends(get_db)):
    return {"message": "DB is working"}


@app.get("/")
def check_connection():
    return {"message": "OK"}
