from fastapi import FastAPI, HTTPException, Depends
from fastapi.routing import APIRouter
from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session

from .db import get_db
from .models import Todo
from .schemas import TodoCreate, TodoUpdate, TodoOut

app = FastAPI()
api = APIRouter(prefix="/api")


@api.get("/health")
def health():
    return {"ok": True}


@api.get("/todos", response_model=list[TodoOut])
def list_todos(db: Session = Depends(get_db)):
    rows = db.execute(select(Todo).order_by(Todo.id.desc())).scalars().all()
    return rows


@api.post("/todos", status_code=201, response_model=TodoOut)
def create_todo(body: TodoCreate, db: Session = Depends(get_db)):
    todo = Todo(title=body.title, done=False)
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


@api.patch("/todos/{todo_id}")
def update_todo(todo_id: int, body: TodoUpdate, db: Session = Depends(get_db)):
    sets = {}
    if body.title is not None:
        sets["title"] = body.title
    if body.done is not None:
        sets["done"] = body.done
    if not sets:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = db.execute(update(Todo).where(Todo.id == todo_id).values(**sets))
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Not found")
    db.commit()
    return {"ok": True}


@api.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    result = db.execute(delete(Todo).where(Todo.id == todo_id))
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Not found")
    db.commit()
    return


app.include_router(api)
