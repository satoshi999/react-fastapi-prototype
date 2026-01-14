from fastapi import FastAPI, HTTPException, Depends
from fastapi.routing import APIRouter
from pydantic import BaseModel
import os
import mysql.connector as mysql
from typing import Generator

from mysql.connector import MySQLConnection
from mysql.connector.cursor import MySQLCursorDict

app = FastAPI()

# APIは /api 配下にまとめる
api = APIRouter(prefix="/api")


def get_db_cursor() -> Generator[MySQLCursorDict, None, None]:
    conn: MySQLConnection | None = None
    cur: MySQLCursorDict | None = None

    try:
        conn = mysql.connect(
            host=os.getenv("DB_HOST", "db"),
            user=os.getenv("DB_USER", "app"),
            password=os.getenv("DB_PASSWORD", "app_pw"),
            database=os.getenv("DB_NAME", "appdb"),
            autocommit=True,
        )
        cur = conn.cursor(dictionary=True)
        yield cur
    finally:
        # cur生成前に落ちても conn は閉じる
        if cur is not None:
            try:
                cur.close()
            except Exception:
                pass
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


class TodoCreate(BaseModel):
    title: str


class TodoUpdate(BaseModel):
    title: str | None = None
    done: bool | None = None


@api.get("/health")
def health():
    return {"ok": True}


@api.get("/todos")
def list_todos(cur: MySQLCursorDict = Depends(get_db_cursor)):
    cur.execute("SELECT id, title, done, created_at FROM todos ORDER BY id DESC")
    rows = cur.fetchall()
    # MySQLの TINYINT(1) を bool に寄せる
    for r in rows:
        r["done"] = bool(r["done"])
    return rows


@api.post("/todos", status_code=201)
def create_todo(body: TodoCreate, cur: MySQLCursorDict = Depends(get_db_cursor)):
    cur.execute("INSERT INTO todos (title, done) VALUES (%s, 0)", (body.title,))
    todo_id = cur.lastrowid
    return {"id": todo_id, "title": body.title, "done": False}


@api.patch("/todos/{todo_id}")
def update_todo(
    todo_id: int, body: TodoUpdate, cur: MySQLCursorDict = Depends(get_db_cursor)
):
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
    cur.execute(f"UPDATE todos SET {', '.join(sets)} WHERE id=%s", vals)
    changed = cur.rowcount
    if changed == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return {"ok": True}


@api.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int, cur: MySQLCursorDict = Depends(get_db_cursor)):
    cur.execute("DELETE FROM todos WHERE id=%s", (todo_id,))
    changed = cur.rowcount
    if changed == 0:
        raise HTTPException(status_code=404, detail="Not found")
    return


app.include_router(api)
