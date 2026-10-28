"""
Tests for API request tracking, unique request IDs, and structured logging.
"""

import logging
import re
from unittest.mock import patch


def test_response_contains_x_request_id(client):
    """Every API response should include a unique X-Request-ID header."""
    response = client.get('/health')
    assert response.status_code == 200
    req_id = response.headers.get('X-Request-ID')
    assert req_id is not None
    assert len(req_id) >= 8


def test_custom_request_id_is_preserved(client):
    """If client sends X-Request-ID, the server preserves and echoes it back."""
    custom_id = "client-trace-abc-12345"
    response = client.get('/health', headers={'X-Request-ID': custom_id})
    assert response.status_code == 200
    assert response.headers.get('X-Request-ID') == custom_id


def test_sequential_requests_generate_unique_ids(client):
    """Sequential requests without client ID generate different IDs."""
    r1 = client.get('/health')
    r2 = client.get('/health')
    id1 = r1.headers.get('X-Request-ID')
    id2 = r2.headers.get('X-Request-ID')
    assert id1 != id2


def test_error_responses_include_request_id(client):
    """Even error responses (e.g. 404, 400) contain X-Request-ID for traceability."""
    r_404 = client.get('/unknown-path')
    assert r_404.status_code == 404
    assert r_404.headers.get('X-Request-ID') is not None

    r_400 = client.post('/api/analyze')
    assert r_400.status_code == 400
    assert r_400.headers.get('X-Request-ID') is not None


def test_cors_exposes_x_request_id(client):
    """CORS Access-Control-Expose-Headers should expose X-Request-ID."""
    # Pre-flight or GET with Origin header
    response = client.get('/health', headers={'Origin': 'http://localhost:5173'})
    expose_headers = response.headers.get('Access-Control-Expose-Headers', '')
    assert 'X-Request-ID' in expose_headers or 'x-request-id' in expose_headers.lower()


def test_request_lifecycle_logging(client, caplog):
    """Verify that request start and completion with status and latency are logged."""
    custom_id = "test-log-id-999"
    with caplog.at_level(logging.INFO):
        response = client.get('/health', headers={'X-Request-ID': custom_id})
        assert response.status_code == 200

    log_messages = [rec.message for rec in caplog.records]
    start_found = any(f"[REQ:{custom_id}] --> GET /health" in msg for msg in log_messages)
    end_found = any(f"[REQ:{custom_id}] <-- GET /health 200" in msg for msg in log_messages)

    assert start_found, f"Expected start log not found in {log_messages}"
    assert end_found, f"Expected completion log with latency not found in {log_messages}"


def test_sensitive_data_not_in_headers(client):
    """Verify headers do not leak sensitive server details or authentication credentials."""
    response = client.get('/health')
    for header_name in response.headers.keys():
        assert 'password' not in header_name.lower()
        assert 'token' not in header_name.lower()
        assert 'secret' not in header_name.lower()
