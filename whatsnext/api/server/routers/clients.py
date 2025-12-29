import re
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.sql.expression import text

from .. import models, schemas
from ..database import get_db

# Maximum items per page to prevent DoS via large queries
MAX_PAGE_SIZE = 1000

# Client ID validation: alphanumeric, hyphens, underscores, max 128 chars
CLIENT_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("/{id}", response_model=schemas.ClientResponse)
def get_client(id: str, db: Session = Depends(get_db)):
    client = db.query(models.Client).filter(models.Client.id == id).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Client with id {id} not found.")
    return client


@router.get("/", response_model=List[schemas.ClientResponse])
def get_clients(
    db: Session = Depends(get_db),
    limit: int = Query(default=100, ge=1, le=MAX_PAGE_SIZE, description="Maximum number of items to return"),
    skip: int = Query(default=0, ge=0, description="Number of items to skip"),
    active_only: bool = True,
):
    query = db.query(models.Client)
    if active_only:
        query = query.filter(models.Client.is_active == 1)
    clients = query.limit(limit).offset(skip).all()
    return clients


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=schemas.ClientResponse)
def register_client(client: schemas.ClientRegister, db: Session = Depends(get_db)):
    """Register a new client or update an existing one with fresh heartbeat."""
    # Validate client ID format
    if not CLIENT_ID_PATTERN.match(client.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid client ID. Must be 1-128 characters, alphanumeric with hyphens and underscores only.",
        )

    existing = db.query(models.Client).filter(models.Client.id == client.id).first()
    if existing:
        # Update existing client
        db.query(models.Client).filter(models.Client.id == client.id).update(
            {
                "name": client.name,
                "entity": client.entity,
                "description": client.description,
                "available_cpu": client.available_cpu,
                "available_accelerators": client.available_accelerators,
                "last_heartbeat": text("now()"),
                "is_active": 1,
            },
            synchronize_session=False,
        )
        db.commit()
        db.refresh(existing)
        return existing

    new_client = models.Client(
        id=client.id,
        name=client.name,
        entity=client.entity,
        description=client.description,
        available_cpu=client.available_cpu,
        available_accelerators=client.available_accelerators,
    )
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    return new_client


@router.post("/{id}/heartbeat", status_code=status.HTTP_200_OK)
def heartbeat(id: str, db: Session = Depends(get_db)):
    """Update client's last heartbeat timestamp."""
    client = db.query(models.Client).filter(models.Client.id == id).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Client with id {id} not found.")

    db.query(models.Client).filter(models.Client.id == id).update({"last_heartbeat": text("now()")}, synchronize_session=False)
    db.commit()
    return {"status": "ok"}


@router.put("/{id}", status_code=status.HTTP_200_OK)
def update_client(id: str, client: schemas.ClientUpdate, db: Session = Depends(get_db)):
    """Update client's resource availability."""
    client_query = db.query(models.Client).filter(models.Client.id == id)
    existing = client_query.first()
    if existing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Client with id {id} not found.")

    update_data = {k: v for k, v in client.model_dump().items() if v is not None}
    if update_data:
        client_query.update(update_data, synchronize_session=False)
        db.commit()
    return {"data": client_query.first()}


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(id: str, db: Session = Depends(get_db)):
    client = db.query(models.Client).filter(models.Client.id == id)
    if client.first() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Client with id {id} not found.")
    client.delete(synchronize_session=False)
    db.commit()


@router.post("/{id}/deactivate", status_code=status.HTTP_200_OK)
def deactivate_client(id: str, db: Session = Depends(get_db)):
    """Mark a client as inactive (graceful disconnect)."""
    client = db.query(models.Client).filter(models.Client.id == id).first()
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Client with id {id} not found.")

    db.query(models.Client).filter(models.Client.id == id).update({"is_active": 0}, synchronize_session=False)
    db.commit()
    return {"status": "deactivated"}
