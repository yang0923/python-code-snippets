# -*- coding: utf-8 -*-
#
# request_sync.py
# @Date   : 2025/6/20 11:30:03
# @Author : yy
# @Des    :  同步请求模块封装，支持 Session（会话）和单请求模式


import logging
import time
from typing import Any, Dict, Optional, Union

import requests

logger = logging.getLogger(__name__)


class SyncHttpClient:
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
        self.session = requests.Session() if use_session else None

    def _full_url(self, url: str) -> str:
        return url if url.startswith("http") else f"{self.base_url}/{url.lstrip('/')}"

    def close(self):
        if self.session:
            self.session.close()

    def _request(
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
                requester = self.session if self.session else requests
                response = requester.request(
                    method=method.upper(),
                    url=full_url,
                    headers=all_headers,
                    params=params,
                    data=data,
                    json=json,
                    timeout=timeout or self.timeout,
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
            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"[{method}] 请求失败 [{attempt}/{self.retry + 1}]: {full_url} -> {e}"
                )
                if attempt < self.retry + 1:
                    time.sleep(self.retry_delay)
                else:
                    return {
                        "success": False,
                        "status_code": getattr(e.response, "status_code", None),
                        "error": str(e),
                    }

    def get(self, url: str, **kwargs) -> Dict[str, Any]:
        return self._request("GET", url, **kwargs)

    def post(self, url: str, **kwargs) -> Dict[str, Any]:
        return self._request("POST", url, **kwargs)

    def put(self, url: str, **kwargs) -> Dict[str, Any]:
        return self._request("PUT", url, **kwargs)

    def delete(self, url: str, **kwargs) -> Dict[str, Any]:
        return self._request("DELETE", url, **kwargs)


if __name__ == "__main__":
    client = SyncHttpClient(
        base_url="https://httpbin.org",
        default_headers={"User-Agent": "MyApp/1.0"},
        retry=2,
        use_session=True,  # 可切换为 False
    )

    # 发起 GET 请求
    resp = client.get("/get", params={"q": "test"})
    print("GET:", resp["data"])

    # 发起 POST 请求
    resp = client.post("/post", json={"name": "alice"})
    print("POST:", resp["data"])

    # 关闭会话
    client.close()
