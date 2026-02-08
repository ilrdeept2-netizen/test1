#!/usr/bin/env python3
"""
Task Management REST API
작업 관리 REST API

A lightweight REST API for creating, reading, updating, and deleting tasks.
Built with Flask and SQLite.
"""

import os
import sqlite3
from datetime import datetime, timezone
from flask import Flask, request, jsonify, g
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DATABASE = os.environ.get('TASK_DB', 'tasks.db')

# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db():
    """Get a database connection for the current request."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """Create the tasks table if it doesn't exist."""
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT    NOT NULL,
            description TEXT    DEFAULT '',
            status      TEXT    NOT NULL DEFAULT 'pending'
                        CHECK(status IN ('pending', 'in_progress', 'completed', 'cancelled')),
            priority    TEXT    NOT NULL DEFAULT 'medium'
                        CHECK(priority IN ('low', 'medium', 'high')),
            due_date    TEXT,
            created_at  TEXT    NOT NULL,
            updated_at  TEXT    NOT NULL
        )
    """)
    db.commit()


def row_to_dict(row):
    """Convert a sqlite3.Row to a plain dict."""
    return dict(row)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

VALID_STATUSES = {'pending', 'in_progress', 'completed', 'cancelled'}
VALID_PRIORITIES = {'low', 'medium', 'high'}


def validate_task_input(data, partial=False):
    """Validate task creation/update payload. Returns (cleaned, error)."""
    if not isinstance(data, dict):
        return None, "Request body must be a JSON object"

    cleaned = {}
    errors = []

    # title
    if 'title' in data:
        title = data['title']
        if not isinstance(title, str) or not title.strip():
            errors.append("'title' must be a non-empty string")
        else:
            cleaned['title'] = title.strip()
    elif not partial:
        errors.append("'title' is required")

    # description
    if 'description' in data:
        cleaned['description'] = str(data['description']).strip()

    # status
    if 'status' in data:
        if data['status'] not in VALID_STATUSES:
            errors.append(f"'status' must be one of {sorted(VALID_STATUSES)}")
        else:
            cleaned['status'] = data['status']

    # priority
    if 'priority' in data:
        if data['priority'] not in VALID_PRIORITIES:
            errors.append(f"'priority' must be one of {sorted(VALID_PRIORITIES)}")
        else:
            cleaned['priority'] = data['priority']

    # due_date (ISO-8601 string or null)
    if 'due_date' in data:
        if data['due_date'] is None:
            cleaned['due_date'] = None
        else:
            try:
                datetime.fromisoformat(str(data['due_date']))
                cleaned['due_date'] = str(data['due_date'])
            except ValueError:
                errors.append("'due_date' must be a valid ISO-8601 date string or null")

    if errors:
        return None, "; ".join(errors)
    return cleaned, None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.before_request
def before_request():
    init_db()


# Health / info ---------------------------------------------------------------

@app.route('/')
def index():
    return jsonify({
        'name': 'Task Management API',
        'version': '1.0.0',
        'endpoints': {
            'GET    /tasks':        'List all tasks (supports filtering & pagination)',
            'POST   /tasks':        'Create a new task',
            'GET    /tasks/<id>':   'Get a single task',
            'PUT    /tasks/<id>':   'Update a task (full replace)',
            'PATCH  /tasks/<id>':   'Partially update a task',
            'DELETE /tasks/<id>':   'Delete a task',
            'GET    /tasks/stats':  'Get task statistics',
            'GET    /health':       'Health check',
        }
    })


@app.route('/health')
def health():
    return jsonify({'status': 'ok'}), 200


# CRUD ------------------------------------------------------------------------

@app.route('/tasks', methods=['GET'])
def list_tasks():
    """
    List tasks with optional filtering and pagination.

    Query params:
      status   - filter by status
      priority - filter by priority
      search   - search title/description (LIKE)
      sort     - field to sort by (default: created_at)
      order    - asc or desc (default: desc)
      page     - page number (default: 1)
      per_page - items per page (default: 20, max 100)
    """
    db = get_db()

    conditions = []
    params = []

    status = request.args.get('status')
    if status:
        if status not in VALID_STATUSES:
            return jsonify({'error': f"Invalid status. Must be one of {sorted(VALID_STATUSES)}"}), 400
        conditions.append("status = ?")
        params.append(status)

    priority = request.args.get('priority')
    if priority:
        if priority not in VALID_PRIORITIES:
            return jsonify({'error': f"Invalid priority. Must be one of {sorted(VALID_PRIORITIES)}"}), 400
        conditions.append("priority = ?")
        params.append(priority)

    search = request.args.get('search')
    if search:
        conditions.append("(title LIKE ? OR description LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    # Sorting
    allowed_sort = {'id', 'title', 'status', 'priority', 'due_date', 'created_at', 'updated_at'}
    sort = request.args.get('sort', 'created_at')
    if sort not in allowed_sort:
        sort = 'created_at'
    order = request.args.get('order', 'desc').lower()
    if order not in ('asc', 'desc'):
        order = 'desc'

    # Pagination
    try:
        page = max(1, int(request.args.get('page', 1)))
    except ValueError:
        page = 1
    try:
        per_page = min(100, max(1, int(request.args.get('per_page', 20))))
    except ValueError:
        per_page = 20
    offset = (page - 1) * per_page

    # Total count
    total = db.execute(f"SELECT COUNT(*) FROM tasks {where}", params).fetchone()[0]

    # Fetch rows
    rows = db.execute(
        f"SELECT * FROM tasks {where} ORDER BY {sort} {order} LIMIT ? OFFSET ?",
        params + [per_page, offset]
    ).fetchall()

    return jsonify({
        'tasks': [row_to_dict(r) for r in rows],
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page,
        }
    })


@app.route('/tasks', methods=['POST'])
def create_task():
    """Create a new task."""
    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Request body must be valid JSON'}), 400

    cleaned, error = validate_task_input(data)
    if error:
        return jsonify({'error': error}), 400

    ts = now_iso()
    db = get_db()
    cursor = db.execute(
        """INSERT INTO tasks (title, description, status, priority, due_date, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        [
            cleaned['title'],
            cleaned.get('description', ''),
            cleaned.get('status', 'pending'),
            cleaned.get('priority', 'medium'),
            cleaned.get('due_date'),
            ts,
            ts,
        ]
    )
    db.commit()

    task = db.execute("SELECT * FROM tasks WHERE id = ?", [cursor.lastrowid]).fetchone()
    return jsonify(row_to_dict(task)), 201


@app.route('/tasks/stats', methods=['GET'])
def task_stats():
    """Return aggregate task statistics."""
    db = get_db()
    total = db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    rows = db.execute("SELECT status, COUNT(*) as count FROM tasks GROUP BY status").fetchall()
    by_status = {r['status']: r['count'] for r in rows}
    rows = db.execute("SELECT priority, COUNT(*) as count FROM tasks GROUP BY priority").fetchall()
    by_priority = {r['priority']: r['count'] for r in rows}

    return jsonify({
        'total': total,
        'by_status': by_status,
        'by_priority': by_priority,
    })


@app.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """Get a single task by ID."""
    db = get_db()
    task = db.execute("SELECT * FROM tasks WHERE id = ?", [task_id]).fetchone()
    if task is None:
        return jsonify({'error': 'Task not found'}), 404
    return jsonify(row_to_dict(task))


@app.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Full update of a task (all fields required)."""
    db = get_db()
    existing = db.execute("SELECT * FROM tasks WHERE id = ?", [task_id]).fetchone()
    if existing is None:
        return jsonify({'error': 'Task not found'}), 404

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Request body must be valid JSON'}), 400

    cleaned, error = validate_task_input(data, partial=False)
    if error:
        return jsonify({'error': error}), 400

    ts = now_iso()
    db.execute(
        """UPDATE tasks
           SET title=?, description=?, status=?, priority=?, due_date=?, updated_at=?
           WHERE id=?""",
        [
            cleaned['title'],
            cleaned.get('description', ''),
            cleaned.get('status', 'pending'),
            cleaned.get('priority', 'medium'),
            cleaned.get('due_date'),
            ts,
            task_id,
        ]
    )
    db.commit()

    task = db.execute("SELECT * FROM tasks WHERE id = ?", [task_id]).fetchone()
    return jsonify(row_to_dict(task))


@app.route('/tasks/<int:task_id>', methods=['PATCH'])
def patch_task(task_id):
    """Partial update of a task."""
    db = get_db()
    existing = db.execute("SELECT * FROM tasks WHERE id = ?", [task_id]).fetchone()
    if existing is None:
        return jsonify({'error': 'Task not found'}), 404

    data = request.get_json(silent=True)
    if data is None:
        return jsonify({'error': 'Request body must be valid JSON'}), 400

    cleaned, error = validate_task_input(data, partial=True)
    if error:
        return jsonify({'error': error}), 400

    if not cleaned:
        return jsonify({'error': 'No valid fields to update'}), 400

    cleaned['updated_at'] = now_iso()

    set_clause = ", ".join(f"{k}=?" for k in cleaned)
    values = list(cleaned.values()) + [task_id]

    db.execute(f"UPDATE tasks SET {set_clause} WHERE id=?", values)
    db.commit()

    task = db.execute("SELECT * FROM tasks WHERE id = ?", [task_id]).fetchone()
    return jsonify(row_to_dict(task))


@app.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task."""
    db = get_db()
    existing = db.execute("SELECT * FROM tasks WHERE id = ?", [task_id]).fetchone()
    if existing is None:
        return jsonify({'error': 'Task not found'}), 404

    db.execute("DELETE FROM tasks WHERE id = ?", [task_id])
    db.commit()
    return jsonify({'message': 'Task deleted', 'id': task_id})


# ---------------------------------------------------------------------------
# Error handlers
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({'error': 'Method not allowed'}), 405


@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    print("=" * 60)
    print("Task Management REST API")
    print("작업 관리 REST API")
    print("=" * 60)
    print()
    print("Server: http://localhost:5001")
    print()
    print("Endpoints:")
    print("  GET    /tasks        - List tasks")
    print("  POST   /tasks        - Create task")
    print("  GET    /tasks/<id>   - Get task")
    print("  PUT    /tasks/<id>   - Update task")
    print("  PATCH  /tasks/<id>   - Partial update")
    print("  DELETE /tasks/<id>   - Delete task")
    print("  GET    /tasks/stats  - Statistics")
    print("  GET    /health       - Health check")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5001, debug=True)
