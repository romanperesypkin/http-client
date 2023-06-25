"""Http client."""
import asyncio
import logging
from typing import Any, Callable, Optional

import orjson
from aiohttp import ClientSession, TCPConnector
from aiohttp.client import _RequestContextManager  # noqa: WPS450
from aiohttp.typedefs import URL
from client.service import Service
from mypy_extensions import Arg, DefaultNamedArg, KwArg
from prometheus_client import Counter


RequestT = dict[str, Any] | Any
RawRequestT = bytes
ResponseT = Any
ParamsT = dict[str, str | int]
TimeoutT = float | int
HeadersT = dict[str, str]
JsonSerializerT = Callable[[Any, Optional[Callable[[Any], Any]], Optional[int]], bytes]
JsonDeserializerT = Callable[[bytes | bytearray | memoryview | str], Any]
PostT = (
    Callable[
        [Arg(str | URL, 'url'), DefaultNamedArg(Any, 'data'), KwArg(Any)],   # noqa: F821
        '_RequestContextManager'
    ]
)
GetT = (
    Callable[
        [Arg(str | URL, 'url'), DefaultNamedArg(Any, 'allow_redirects'), KwArg(Any)],  # noqa: F821
        '_RequestContextManager'
    ]
)


HTTP_200_OK = 200
DEFAULT_POST_HEADERS = {  # noqa: WPS407
    'Content-Type': 'application/json',
    'accept': 'application/json'
}
DEFAULT_GET_HEADERS = {  # noqa: WPS407
    'accept': 'application/json'
}


class HttpClient(Service):
    """Http client wrapper over aio-http."""

    def __init__(
        self,
        app_name: str,
        http_connection_limit: int,
        http_request_timeout: TimeoutT,
        json_serialize: Callable[[Any], bytes] = orjson.dumps,
        json_deserialize: JsonDeserializerT = orjson.loads,
        log_name: str = 'dwh_http_client'
    ):
        """Consturctor.

        :param app_name: app name
        :param http_connection_limit: session connection limit
        :param http_request_timeout: request timeout
        :param log_name: default log name
        :param json_serialize: Callbale to serialize data into json
        :param json_deserialize: Callbale to deserialize data from json
        """
        self.log = logging.getLogger(log_name)
        self.app_name = app_name
        self.http_connection_limit = http_connection_limit
        self.http_request_timeout = http_request_timeout
        self.json_serialize = json_serialize
        self.json_deserialize = json_deserialize
        self.session = ClientSession(
            connector=TCPConnector(limit=self.http_connection_limit, force_close=True),
            timeout=self.http_request_timeout
        )

        metric_labels = ['app_name', 'url']
        self.http_requests_failed = Counter('http_requests_failed', 'Count requests failed', metric_labels)
        self.http_requests_timeout = Counter('http_requests_timeout', 'Count requests timed out', metric_labels)
        self.http_exceptions = Counter('http_exceptions', 'Count of exceptions', metric_labels)

    async def stop(self) -> None:
        """Stop service."""
        if self.session:
            await self.session.close()

    async def post(
        self,
        url: str,
        request: RequestT,
        headers: HeadersT | None = DEFAULT_POST_HEADERS,
        timeout: TimeoutT | None = None,
    ) -> ResponseT | None:
        """Post request.

        :param url: request url
        :param request: json to send
        :param headers: http headers
        :param timeout: time to wait for response
        :return: json response or None
        """
        return await self._do_request(
            self.session.post,
            url,
            request=self.json_serialize(request),
            headers=headers,
            timeout=timeout
        )

    async def get(
        self,
        url: str,
        params: ParamsT | None = None,
        headers: HeadersT | None = DEFAULT_GET_HEADERS,
        timeout: TimeoutT | None = None
    ) -> ResponseT | None:
        """Get request.

        :param url: request url
        :param params: key value pairs to be used as query string
        :param headers: http headers
        :param timeout: time to wait for response
        :return: json response or None
        """
        return await self._do_request(
            self.session.get,
            url,
            params=params,
            headers=headers,
            timeout=timeout
        )

    async def _do_request(
        self,
        method: PostT | GetT,
        url: str,
        request: RawRequestT | None = None,
        params: ParamsT | None = None,
        headers: HeadersT | None = None,
        timeout: TimeoutT | None = None
    ) -> ResponseT | None:
        """Actual request send.

        :param method: aiohttp session method e.g. post, get
        :param url: request url
        :param request: json to send
        :param params: key value pairs to be used as query string
        :param headers: http headers
        :param timeout: time to wait for response
        :return: json response or None
        """
        try:
            async with method(
                url,
                data=request,
                params=params,
                headers=headers,
                timeout=timeout,
                ssl=False,
            ) as response:
                if response.status == HTTP_200_OK:
                    raw_data = await response.read()
                    return self.json_deserialize(raw_data)
                text = await response.text()
                self.http_requests_failed.labels(self.app_name, url).inc()
                self.log.warning('Request failed', extra={'status': response.status, 'text': text, 'url': url})
        except asyncio.TimeoutError:
            self.http_requests_timeout.labels(self.app_name, url).inc()
            self.log.exception('Request timed out', extra={'url': url})
        except Exception:
            self.http_exceptions.labels(self.app_name, url).inc()
            self.log.exception('Request exception', extra={'url': url})
        return None
