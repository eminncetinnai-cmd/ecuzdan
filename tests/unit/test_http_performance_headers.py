"""Tests for HTTP Security, Static Asset Caching, and GZIP Response Compression."""

import gzip

from flask import Flask

from routes import register_security_headers


def test_static_asset_immutable_cache():
    """Test versioned static assets receive 1-year immutable cache header."""
    app = Flask(__name__)
    app.config['TESTING'] = False
    app.config['TEMPLATES_AUTO_RELOAD'] = False
    register_security_headers(app)

    @app.route('/static/test.css')
    def dummy_static():
        return "body { color: red; }", 200, {'Content-Type': 'text/css'}

    client = app.test_client()

    # Versioned asset
    r_versioned = client.get('/static/test.css?v=abc12345')
    assert 'max-age=31536000' in r_versioned.headers.get('Cache-Control', '')
    assert 'immutable' in r_versioned.headers.get('Cache-Control', '')

    # Non-versioned asset
    r_non_versioned = client.get('/static/test.css')
    assert 'max-age=604800' in r_non_versioned.headers.get('Cache-Control', '')


def test_gzip_compression_on_large_json():
    """Test large responses (>500 bytes) are gzip compressed when requested."""
    app = Flask(__name__)
    register_security_headers(app)

    @app.route('/large-data')
    def large_data():
        return {"items": ["item_" + str(i) for i in range(200)]}

    client = app.test_client()

    # Request without gzip
    r_raw = client.get('/large-data')
    assert 'Content-Encoding' not in r_raw.headers
    raw_len = len(r_raw.data)
    assert raw_len > 500

    # Request with gzip
    r_gzip = client.get('/large-data', headers={'Accept-Encoding': 'gzip, deflate'})
    assert r_gzip.headers.get('Content-Encoding') == 'gzip'
    assert r_gzip.headers.get('Vary') == 'Accept-Encoding'
    compressed_len = len(r_gzip.data)
    assert compressed_len < raw_len

    # Verify decompressed payload matches raw payload
    decompressed = gzip.decompress(r_gzip.data)
    assert decompressed == r_raw.data


def test_no_gzip_on_small_response():
    """Test small responses (<500 bytes) are not compressed to avoid compression overhead."""
    app = Flask(__name__)
    register_security_headers(app)

    @app.route('/small-data')
    def small_data():
        return {"status": "ok"}

    client = app.test_client()
    r = client.get('/small-data', headers={'Accept-Encoding': 'gzip'})
    assert 'Content-Encoding' not in r.headers
