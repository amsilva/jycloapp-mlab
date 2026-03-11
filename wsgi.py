"""
WSGI entry point for PythonAnywhere.

FastAPI is ASGI. PythonAnywhere uses uWSGI (WSGI).
This file bridges them manually using asyncio.run() — no extra dependencies needed.
"""
import sys
import os
import asyncio

project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# --- SET YOUR CREDENTIALS HERE ---
os.environ.setdefault('DATABASE_URL', 'mysql+pymysql://lab43:SUA_SENHA@lab43.mysql.pythonanywhere-services.com/lab43$jycloapp')
os.environ.setdefault('SECRET_KEY', 'sua-chave-secreta-aqui')
# ----------------------------------

from app.main import app as fastapi_app


def application(environ, start_response):
    """Manual ASGI-to-WSGI bridge using asyncio.run()."""

    method = environ['REQUEST_METHOD']
    path = environ.get('PATH_INFO', '/')
    query = environ.get('QUERY_STRING', b'')
    if isinstance(query, str):
        query = query.encode('latin-1')

    # Build headers list
    headers = []
    for key, value in environ.items():
        if key.startswith('HTTP_'):
            name = key[5:].lower().replace('_', '-').encode('latin-1')
            headers.append((name, value.encode('latin-1')))
    content_type = environ.get('CONTENT_TYPE', '')
    if content_type:
        headers.append((b'content-type', content_type.encode('latin-1')))
    content_length_str = environ.get('CONTENT_LENGTH', '')
    content_length = int(content_length_str) if content_length_str else 0
    if content_length:
        headers.append((b'content-length', str(content_length).encode('latin-1')))

    # Read request body
    body = environ['wsgi.input'].read(content_length) if content_length else b''

    # Build ASGI scope
    scope = {
        'type': 'http',
        'asgi': {'version': '3.0'},
        'http_version': '1.1',
        'method': method,
        'path': path,
        'raw_path': path.encode('latin-1'),
        'root_path': environ.get('SCRIPT_NAME', ''),
        'query_string': query,
        'headers': headers,
        'server': (environ.get('SERVER_NAME', 'localhost'), int(environ.get('SERVER_PORT', 80))),
    }

    # Collectors for the ASGI response
    response_status = []
    response_headers = []
    response_body = []

    async def receive():
        return {'type': 'http.request', 'body': body, 'more_body': False}

    async def send(message):
        if message['type'] == 'http.response.start':
            response_status.append(message['status'])
            response_headers.extend(message.get('headers', []))
        elif message['type'] == 'http.response.body':
            response_body.append(message.get('body', b''))

    # Run the ASGI app synchronously
    asyncio.run(fastapi_app(scope, receive, send))

    status_code = response_status[0] if response_status else 500
    raw_headers = [
        (k.decode('latin-1'), v.decode('latin-1'))
        for k, v in response_headers
    ]
    start_response(f'{status_code} OK', raw_headers)
    return response_body
