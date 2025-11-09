from fastapi import FastAPI, HTTPException
from fastapi.routing import APIRouter
from pydantic import BaseModel
import os
import mysql.connector as mysql

app = FastAPI()


def get_db():
    return mysql.connect(
        host=os.getenv("DB_HOST", "db"),
        user=os.getenv("DB_USER", "app"),
        password=os.getenv("DB_PASSWORD", "app_pw"),
        database=os.getenv("DB_NAME", "appdb"),
        autocommit=True,
    )


class TodoCreate(BaseModel):
    title: str


class TodoUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/todos")
def list_todos():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT id, title, done, created_at FROM todos ORDER BY id DESC")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    # MySQLの TINYINT(1) を bool に寄せる
    for r in rows:
        r["done"] = bool(r["done"])
    return rows


@app.post("/todos", status_code=201)
def create_todo(body: TodoCreate):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO todos (title, done) VALUES (%s, 0)", (body.title,))
    todo_id = cur.lastrowid
    cur.close()
    conn.close()
    return {"id": todo_id, "title": body.title, "done": False}


@app.patch("/todos/{todo_id}")
def update_todo(todo_id: int, body: TodoUpdate):
    sets = []
    vals = []
    if body.title is not None:
        sets.append("title=%s")
        vals.append(body.title)
    if body.done is not None:
        sets.append("done=%s")
        vals.append(1 if body.done else 0)
    if not sets:
        raise HTTPException(status_code=400, detail="No fields to update")

    vals.append(todo_id)
    conn = get_db()
    cur = conn.cursor()
    cur.execute(f"UPDATE todos SET {', '.join(sets)} WHERE id=%s", vals)
    changed = cur.rowcount
    cur.close()
    conn.close()
    if changed == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"ok": True}


@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM todos WHERE id=%s", (todo_id,))
    changed = cur.rowcount
    cur.close()
    conn.close()
    if changed == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return
