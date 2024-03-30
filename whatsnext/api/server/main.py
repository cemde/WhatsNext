from fastapi import FastAPI, Response, Depends
from sqlalchemy.orm import Session

from . import models
from .database import engine, get_db
from .routers import jobs, projects

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(jobs.router)
# app.include_router(projects.router)


@app.get("/")
async def root1():
    return {"message": "App 1"}


@app.get("/checkdb")
def check_db(response: Response, db: Session = Depends(get_db)):
    return {"message": "DB is working"}
