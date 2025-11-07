import { useEffect, useMemo, useState } from 'react'
import './App.css'

type Todo = {
  id: number
  title: string
  done: boolean
  created_at?: string
}

// 今開いているページのオリジンをそのままAPIのベースURLに使う
const API_BASE = `${window.location.origin}/api`


export default function App() {
  return (
    <TodoApp />
  )
}

function TodoApp() {
  const [todos, setTodos] = useState<Todo[]>([])
  const [newTitle, setNewTitle] = useState('')
  const [loading, setLoading] = useState(false)
  const base = useMemo(() => API_BASE.replace(/\/+$/, ''), [])

  async function fetchTodos() {
    setLoading(true)
    try {
      const res = await fetch(`${base}/todos`)
      const data = await res.json()
      setTodos(data)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTodos()
  }, [])

  async function addTodo(e: React.FormEvent) {
    e.preventDefault()
    const title = newTitle.trim()
    if (!title) return
    const res = await fetch(`${base}/todos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    })
    if (res.ok) {
      setNewTitle('')
      fetchTodos()
    }
  }

  async function toggleDone(t: Todo) {
    await fetch(`${base}/todos/${t.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ done: !t.done }),
    })
    fetchTodos()
  }

  async function rename(t: Todo, title: string) {
    const val = title.trim()
    if (!val || val === t.title) return
    await fetch(`${base}/todos/${t.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: val }),
    })
    fetchTodos()
  }

  async function remove(t: Todo) {
    await fetch(`${base}/todos/${t.id}`, { method: 'DELETE' })
    fetchTodos()
  }

  return (
    <div style={{ padding: 24, maxWidth: 720, margin: '0 auto' }}>
      <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 16 }}>
        <h1 style={{ margin: 0, fontSize: 22 }}>Todo manage app</h1>
      </div>

      <form onSubmit={addTodo} style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
        <input
          value={newTitle}
          onChange={(e) => setNewTitle(e.target.value)}
          placeholder="Add a new todo..."
          style={{ flex: 1, padding: 8 }}
        />
        <button type="submit">Add</button>
      </form>

      {loading ? (
        <p>Loading...</p>
      ) : todos.length === 0 ? (
        <p>No todos</p>
      ) : (
        <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
          {todos.map((t) => (
            <li key={t.id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 0', borderBottom: '1px solid #eee' }}>
              <input type="checkbox" checked={t.done} onChange={() => toggleDone(t)} />
              <EditableText
                text={t.title}
                onSave={(val) => rename(t, val)}
                style={{ flex: 1 }}
              />
              <button onClick={() => remove(t)}>Delete</button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function EditableText({
  text,
  onSave,
  style,
}: {
  text: string
  onSave: (v: string) => void
  style?: React.CSSProperties
}) {
  const [editing, setEditing] = useState(false)
  const [val, setVal] = useState(text)
  useEffect(() => setVal(text), [text])

  if (!editing) {
    return (
      <span style={{ cursor: 'text', ...style }} onClick={() => setEditing(true)} title="Click to edit">
        {text}
      </span>
    )
  }
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault()
        setEditing(false)
        onSave(val)
      }}
      style={{ flex: 1 }}
    >
      <input
        autoFocus
        value={val}
        onChange={(e) => setVal(e.target.value)}
        onBlur={() => {
          setEditing(false)
          onSave(val)
        }}
        style={{ width: '100%', padding: 4 }}
      />
    </form>
  )
}