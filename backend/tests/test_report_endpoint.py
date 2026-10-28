"""
Tests for PDF report generation and download endpoint: POST /api/report.
"""

from unittest.mock import patch
from report_generator import generate_analysis_pdf


def test_report_endpoint_missing_payload_returns_400(client):
    """POST /api/report with no json payload returns 400."""
    response = client.post('/api/report', json={})
    assert response.status_code == 400
    data = response.get_json()
    assert data.get('error') == 'invalid_payload'


def test_report_endpoint_empty_results_returns_400(client):
    """POST /api/report with empty results list returns 400."""
    response = client.post('/api/report', json={'results': []})
    assert response.status_code == 400
    data = response.get_json()
    assert data.get('error') == 'invalid_payload'


def test_report_endpoint_success_returns_pdf(client):
    """POST /api/report with valid results returns a binary PDF stream with attachment header."""
    payload = {
        'model_used': 'CheXNet',
        'scan_type': 'chest',
        'results': [
            {
                'disease': 'Pneumonia',
                'confidence': 88,
                'status': 'critical',
                'description': 'Bilateral opacity detected in right lower lung.',
                'regions': ['right lower lobe'],
                'uncertainty_pct': 4,
                'final_assessment': 'Findings suggest active bacterial pneumonia consolidation.'
            },
            {
                'disease': 'Infiltration',
                'confidence': 54,
                'status': 'warning',
                'description': 'Secondary parenchymal opacity.'
            }
        ]
    }
    response = client.post('/api/report', json=payload)
    assert response.status_code == 200
    assert response.mimetype == 'application/pdf'
    assert 'attachment' in response.headers.get('Content-Disposition', '')
    assert 'mediscan_report_' in response.headers.get('Content-Disposition', '')
    assert response.data.startswith(b'%PDF')


def test_report_endpoint_handles_missing_fields_gracefully(client):
    """Report compiles safely even when optional result fields are absent."""
    minimal_payload = {
        'results': [
            {
                'disease': 'Normal',
                'confidence': 95,
                'status': 'healthy'
                # Notice: description, regions, final_assessment, uncertainty are all missing
            }
        ]
    }
    response = client.post('/api/report', json=minimal_payload)
    assert response.status_code == 200
    assert response.mimetype == 'application/pdf'
    assert response.data.startswith(b'%PDF')


def test_report_generator_direct_pdf_structure():
    """Direct test of generate_analysis_pdf ensuring proper PDF byte generation."""
    sample_data = {
        'model_used': 'TuberculosisNet',
        'scan_type': 'Chest X-ray',
        'results': [
            {
                'disease': 'Tuberculosis',
                'confidence': 91,
                'status': 'critical',
                'description': 'Apical cavitation pattern observed.',
                'regions': ['left apex'],
                'warnings': ['low_image_quality']
            }
        ]
    }
    pdf_bytes = generate_analysis_pdf(sample_data)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b'%PDF')
    assert len(pdf_bytes) > 500


def test_report_endpoint_server_error_returns_500(client):
    """POST /api/report returns 500 if PDF compiler encounters an unexpected exception."""
    with patch('app.generate_analysis_pdf', side_effect=RuntimeError("Font rendering engine crash")):
        response = client.post('/api/report', json={'results': [{'disease': 'Test', 'confidence': 50}]})
        assert response.status_code == 500
        data = response.get_json()
        assert data.get('error') == 'report_generation_failed'
