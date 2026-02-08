#!/usr/bin/env python3
"""
Tests for the Task Management REST API
작업 관리 REST API 테스트
"""

import json
import os
import tempfile
import unittest

# Use a temporary database for each test run
TEST_DB = tempfile.mktemp(suffix='.db')
os.environ['TASK_DB'] = TEST_DB

from task_api import app


class TaskAPITestCase(unittest.TestCase):
    """Base test case with helper methods."""

    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        # Reset DB for each test
        if os.path.exists(TEST_DB):
            os.unlink(TEST_DB)

    def tearDown(self):
        if os.path.exists(TEST_DB):
            os.unlink(TEST_DB)

    def create_task(self, **kwargs):
        payload = {
            'title': kwargs.get('title', 'Test task'),
            'description': kwargs.get('description', 'A test task'),
            'status': kwargs.get('status', 'pending'),
            'priority': kwargs.get('priority', 'medium'),
        }
        if 'due_date' in kwargs:
            payload['due_date'] = kwargs['due_date']
        return self.client.post('/tasks', json=payload)

    # ------------------------------------------------------------------
    # Index / Health
    # ------------------------------------------------------------------

    def test_index(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['name'], 'Task Management API')

    def test_health(self):
        resp = self.client.get('/health')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['status'], 'ok')

    # ------------------------------------------------------------------
    # CREATE
    # ------------------------------------------------------------------

    def test_create_task(self):
        resp = self.create_task(title='Buy groceries', priority='high')
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertEqual(data['title'], 'Buy groceries')
        self.assertEqual(data['priority'], 'high')
        self.assertEqual(data['status'], 'pending')
        self.assertIn('id', data)
        self.assertIn('created_at', data)

    def test_create_task_minimal(self):
        resp = self.client.post('/tasks', json={'title': 'Minimal'})
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertEqual(data['title'], 'Minimal')
        self.assertEqual(data['status'], 'pending')
        self.assertEqual(data['priority'], 'medium')

    def test_create_task_missing_title(self):
        resp = self.client.post('/tasks', json={'description': 'no title'})
        self.assertEqual(resp.status_code, 400)

    def test_create_task_empty_title(self):
        resp = self.client.post('/tasks', json={'title': '   '})
        self.assertEqual(resp.status_code, 400)

    def test_create_task_invalid_status(self):
        resp = self.create_task(status='invalid')
        self.assertEqual(resp.status_code, 400)

    def test_create_task_invalid_priority(self):
        resp = self.create_task(priority='urgent')
        self.assertEqual(resp.status_code, 400)

    def test_create_task_invalid_json(self):
        resp = self.client.post('/tasks', data='not json',
                                content_type='application/json')
        self.assertEqual(resp.status_code, 400)

    def test_create_task_with_due_date(self):
        resp = self.create_task(due_date='2026-03-01T00:00:00')
        self.assertEqual(resp.status_code, 201)
        data = resp.get_json()
        self.assertEqual(data['due_date'], '2026-03-01T00:00:00')

    def test_create_task_invalid_due_date(self):
        resp = self.create_task(due_date='not-a-date')
        self.assertEqual(resp.status_code, 400)

    # ------------------------------------------------------------------
    # READ
    # ------------------------------------------------------------------

    def test_get_task(self):
        create_resp = self.create_task(title='Read me')
        task_id = create_resp.get_json()['id']
        resp = self.client.get(f'/tasks/{task_id}')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()['title'], 'Read me')

    def test_get_task_not_found(self):
        resp = self.client.get('/tasks/9999')
        self.assertEqual(resp.status_code, 404)

    def test_list_tasks_empty(self):
        resp = self.client.get('/tasks')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['tasks'], [])
        self.assertEqual(data['pagination']['total'], 0)

    def test_list_tasks(self):
        self.create_task(title='Task 1')
        self.create_task(title='Task 2')
        self.create_task(title='Task 3')
        resp = self.client.get('/tasks')
        data = resp.get_json()
        self.assertEqual(len(data['tasks']), 3)
        self.assertEqual(data['pagination']['total'], 3)

    # ------------------------------------------------------------------
    # FILTER & SEARCH
    # ------------------------------------------------------------------

    def test_filter_by_status(self):
        self.create_task(title='A', status='pending')
        self.create_task(title='B', status='completed')
        resp = self.client.get('/tasks?status=completed')
        tasks = resp.get_json()['tasks']
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['title'], 'B')

    def test_filter_by_priority(self):
        self.create_task(title='Low', priority='low')
        self.create_task(title='High', priority='high')
        resp = self.client.get('/tasks?priority=high')
        tasks = resp.get_json()['tasks']
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['title'], 'High')

    def test_search(self):
        self.create_task(title='Buy milk')
        self.create_task(title='Read book')
        resp = self.client.get('/tasks?search=milk')
        tasks = resp.get_json()['tasks']
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['title'], 'Buy milk')

    def test_filter_invalid_status(self):
        resp = self.client.get('/tasks?status=bogus')
        self.assertEqual(resp.status_code, 400)

    # ------------------------------------------------------------------
    # PAGINATION
    # ------------------------------------------------------------------

    def test_pagination(self):
        for i in range(25):
            self.create_task(title=f'Task {i}')
        resp = self.client.get('/tasks?per_page=10&page=1')
        data = resp.get_json()
        self.assertEqual(len(data['tasks']), 10)
        self.assertEqual(data['pagination']['total'], 25)
        self.assertEqual(data['pagination']['pages'], 3)

    # ------------------------------------------------------------------
    # UPDATE (PUT)
    # ------------------------------------------------------------------

    def test_update_task(self):
        create_resp = self.create_task(title='Old title')
        task_id = create_resp.get_json()['id']
        resp = self.client.put(f'/tasks/{task_id}', json={
            'title': 'New title',
            'description': 'Updated',
            'status': 'in_progress',
            'priority': 'high',
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['title'], 'New title')
        self.assertEqual(data['status'], 'in_progress')

    def test_update_task_not_found(self):
        resp = self.client.put('/tasks/9999', json={'title': 'X'})
        self.assertEqual(resp.status_code, 404)

    def test_update_task_missing_title(self):
        create_resp = self.create_task()
        task_id = create_resp.get_json()['id']
        resp = self.client.put(f'/tasks/{task_id}', json={'description': 'no title'})
        self.assertEqual(resp.status_code, 400)

    # ------------------------------------------------------------------
    # PARTIAL UPDATE (PATCH)
    # ------------------------------------------------------------------

    def test_patch_task(self):
        create_resp = self.create_task(title='Original')
        task_id = create_resp.get_json()['id']
        resp = self.client.patch(f'/tasks/{task_id}', json={'status': 'completed'})
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['status'], 'completed')
        self.assertEqual(data['title'], 'Original')  # unchanged

    def test_patch_task_not_found(self):
        resp = self.client.patch('/tasks/9999', json={'status': 'completed'})
        self.assertEqual(resp.status_code, 404)

    def test_patch_task_empty(self):
        create_resp = self.create_task()
        task_id = create_resp.get_json()['id']
        resp = self.client.patch(f'/tasks/{task_id}', json={})
        self.assertEqual(resp.status_code, 400)

    # ------------------------------------------------------------------
    # DELETE
    # ------------------------------------------------------------------

    def test_delete_task(self):
        create_resp = self.create_task(title='Delete me')
        task_id = create_resp.get_json()['id']
        resp = self.client.delete(f'/tasks/{task_id}')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('deleted', resp.get_json()['message'].lower())
        # Verify gone
        resp = self.client.get(f'/tasks/{task_id}')
        self.assertEqual(resp.status_code, 404)

    def test_delete_task_not_found(self):
        resp = self.client.delete('/tasks/9999')
        self.assertEqual(resp.status_code, 404)

    # ------------------------------------------------------------------
    # STATS
    # ------------------------------------------------------------------

    def test_stats_empty(self):
        resp = self.client.get('/tasks/stats')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['total'], 0)

    def test_stats(self):
        self.create_task(status='pending', priority='low')
        self.create_task(status='pending', priority='high')
        self.create_task(status='completed', priority='high')
        resp = self.client.get('/tasks/stats')
        data = resp.get_json()
        self.assertEqual(data['total'], 3)
        self.assertEqual(data['by_status']['pending'], 2)
        self.assertEqual(data['by_status']['completed'], 1)
        self.assertEqual(data['by_priority']['high'], 2)
        self.assertEqual(data['by_priority']['low'], 1)


if __name__ == '__main__':
    unittest.main()
