import asyncio
import base64
import json
from functools import wraps
from io import BytesIO
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Tuple
from urllib.parse import urlparse, urlunparse
from zipfile import ZIP_DEFLATED, ZipFile

from aiohttp import ClientResponse, ClientSession
from structlog import get_logger


log = get_logger()


def wrap_screen(data):
    """
    Data returned from a webdriver may contain a screen, which is a base64
    encoded PNG of the browser screen. This is a massive string and will make
    logging useless, so we wrap it in a BytesIO.
    """
    if isinstance(data, dict) and 'value' in data and isinstance(data['value'], dict) and 'screen' in data['value'] and data['value']['screen']:
        data['value']['screen'] = BytesIO(base64.b64decode(data['value']['screen']))


def ensure_task(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.get_event_loop().create_task(func(*args, **kwargs))
    return wrapper


def strip_auth(url: str) -> str:
    pr = urlparse(url)
    safe_netloc = pr.hostname
    if pr.port:
        safe_netloc = f'{safe_netloc}:{pr.port}'
    return urlunparse((pr.scheme, safe_netloc, pr.path, pr.params, pr.query, pr.fragment))


class Connection:
    def __init__(self, session: ClientSession, prefix: str):
        self.session = session
        self.prefix = prefix

    @ensure_task
    async def request(self, *, url: str, method: str, data=None) -> Tuple[int, Any]:
        if data is None:
            data = {}
        if method not in {'POST', 'PUT'}:
            data = None
        body = json.dumps(data) if data is not None else None
        full_url = self.prefix + url
        log.info('request', url=strip_auth(full_url), method=method, body=body)
        response: ClientResponse = await self.session.request(
            url=full_url,
            method=method,
            data=body
        )
        response_body = await response.read()
        try:
            data = json.loads(response_body)
        except JSONDecodeError as exc:
            log.error('json-decode', body=response_body)
            data = {
                'error': '!internal',
                'message': str(exc),
                'stacktrace': ''
            }
        wrap_screen(data)
        log.info('response', url=strip_auth(full_url), method=method, body=body, response=response, data=data)
        return response.status, data

    async def upload_file(self, path: Path) -> Path:
        log.info('upload-file', path=path, resolved_path=path)
        return path

    def prefixed(self, prefix: str) -> 'Connection':
        return self.__class__(self.session, self.prefix + prefix)


class RemoteConnection(Connection):
    async def upload_file(self, path: Path) -> Path:
        fobj = BytesIO()
        with ZipFile(fobj, 'w', ZIP_DEFLATED) as zf:
            zf.write(path, path.name)
        content = base64.b64encode(fobj.getvalue()).decode('utf-8')
        resolved = await self.request(
            url='/file',
            method='POST',
            data={
                'file': content
            }
        )
        log.info('upload-file', path=path, resolved_path=resolved)
        return resolved
