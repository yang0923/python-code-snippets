# -*- coding: utf-8 -*-
#
# request_async.py
# @Date   : 2025/6/20 11:43:52
# @Author : yy
# @Des    : 异步请求模块封装，支持 AsyncClient 会话和单请求模式
import asyncio
import logging
from typing import Any, Dict, Optional, Union

import httpx

logger = logging.getLogger(__name__)


class AsyncHttpClient:
    def __init__(
        self,
        base_url: str = "",
        default_headers: Optional[Dict[str, str]] = None,
        timeout: int = 10,
        retry: int = 2,
        retry_delay: float = 0.5,
        use_session: bool = True,
    ):
        self.base_url = base_url.rstrip("/")
        self.default_headers = default_headers or {}
        self.timeout = timeout
        self.retry = retry
        self.retry_delay = retry_delay
        self.use_session = use_session
        self.client = httpx.AsyncClient(timeout=self.timeout) if use_session else None

    def _full_url(self, url: str) -> str:
        return url if url.startswith("http") else f"{self.base_url}/{url.lstrip('/')}"

    async def close(self):
        if self.client:
            await self.client.aclose()

    async def _request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Union[Dict, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        full_url = self._full_url(url)
        all_headers = self.default_headers.copy()
        if headers:
            all_headers.update(headers)

        for attempt in range(1, self.retry + 2):
            try:
                if self.client:
                    response = await self.client.request(
                        method=method.upper(),
                        url=full_url,
                        headers=all_headers,
                        params=params,
                        data=data,
                        json=json,
                        timeout=timeout or self.timeout,
                        **kwargs,
                    )
                else:
                    async with httpx.AsyncClient(
                        timeout=timeout or self.timeout
                    ) as temp_client:
                        response = await temp_client.request(
                            method=method.upper(),
                            url=full_url,
                            headers=all_headers,
                            params=params,
                            data=data,
                            json=json,
                            **kwargs,
                        )
                response.raise_for_status()
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "data": response.json()
                    if "application/json" in response.headers.get("Content-Type", "")
                    else response.text,
                }
            except httpx.RequestError as e:
                logger.warning(
                    f"[{method}] 请求失败 [{attempt}/{self.retry + 1}]: {full_url} -> {e}"
                )
                if attempt < self.retry + 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    return {
                        "success": False,
                        "status_code": None,
                        "error": str(e),
                    }

    async def get(self, url: str, **kwargs) -> Dict[str, Any]:
        return await self._request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs) -> Dict[str, Any]:
        return await self._request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs) -> Dict[str, Any]:
        return await self._request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs) -> Dict[str, Any]:
        return await self._request("DELETE", url, **kwargs)


if __name__ == "__main__":

    async def main():
        client = AsyncHttpClient(
            base_url="https://httpbin.org",
            default_headers={"User-Agent": "MyAsyncApp/1.0"},
            retry=2,
            use_session=False,  # 可切换为 False
        )

        resp = await client.get("/get", params={"q": "async"})
        print("GET:", resp)

        resp = await client.post("/post", json={"name": "bob"})
        print("POST:", resp)

        await client.close()

    asyncio.run(main())
