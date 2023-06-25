"""Tests for the HttpClient class."""
import asyncio
from typing import TYPE_CHECKING
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from client.http import HttpClient, RequestT


# All test coroutines will be treated as marked.
pytestmark = pytest.mark.asyncio

HTTP_OK = 200
HTTP_NOT_FOUND = 404


class TestHttpClient(IsolatedAsyncioTestCase):
    """Test class with tests."""

    @patch('client.http.Counter', Mock())
    @patch('client.http.TCPConnector', Mock())
    @patch('client.http.ClientSession', MagicMock())
    def setUp(self) -> None:
        """Prepare fixture."""
        self.client = HttpClient('test', 1, 2)
        self.client.session = MagicMock()
        self.session = self.client.session
        self.data: RequestT = {'test': 'test'}
        self.response_data = b'{"test":"test"}'

    async def test_post_timeout(self) -> None:
        """Test post rise asyncio.TimeoutError."""
        self.session.post('test').__aenter__ = AsyncMock(side_effect=asyncio.TimeoutError)
        response = await self.client.post('test', self.data)
        self.assertIsNone(response)

    async def test_post_random_exception(self) -> None:
        """Test post rise random Exception."""
        self.session.post('test').__aenter__ = AsyncMock(side_effect=ZeroDivisionError)
        response = await self.client.post('test', self.data)
        self.assertIsNone(response)

    async def test_post_status_not_200(self) -> None:
        """Test post response is not 200."""
        mocked_response = AsyncMock(status=HTTP_NOT_FOUND)
        self.session.post('test').__aenter__ = AsyncMock(return_value=mocked_response)
        response = await self.client.post('test', self.data)
        self.assertIsNone(response)

    async def test_post_status_200(self) -> None:
        """Test post respons 200 with json data."""
        self.prepare_mock(self.session.post)
        response = await self.client.post('test', self.data)
        if TYPE_CHECKING:
            assert response is not None  # noqa: S101
        self.assertDictEqual(self.data, response)

    async def test_get_status_200_without_params(self) -> None:
        """Test get respons 200."""
        self.prepare_mock(self.session.get)
        response = await self.client.get('test')
        if TYPE_CHECKING:
            assert response is not None  # noqa: S101
        self.assertDictEqual(self.data, response)

    async def test_get_status_200_with_params(self) -> None:
        """Test post respons 200 with params."""
        self.prepare_mock(self.session.get)
        response = await self.client.get('test', params=self.data)
        if TYPE_CHECKING:
            assert response is not None  # noqa: S101
        self.assertDictEqual(self.data, response)

    def prepare_mock(self, method: MagicMock) -> None:
        """Prepare complex mocks.

        :param method: magic mock to use as http method
        """
        mocked_response = AsyncMock(status=HTTP_OK)
        mocked_response.read = AsyncMock(return_value=self.response_data)
        method().__aenter__ = AsyncMock(return_value=mocked_response)
