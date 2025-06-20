# 网络相关工具

-   [1. 同步HTTP客户端](#1-同步http客户端)
-   [2. 异步HTTP客户端](#2-异步http客户端)

---

## 1. [同步HTTP客户端](request_sync.py)

[`request_sync.py`](request_sync.py) 是一个基于 `requests` 库的同步 HTTP 请求模块封装，适用于需要会话管理和重试机制的各种 Python 项目，提供简洁统一的接口支持 `GET`/`POST`/`PUT`/`DELETE` 等常用 HTTP 方法。

### 1.1 ⚙️ 主要功能

-   ✅ 支持基于 Session 的会话请求，保持连接和 Cookie
-   ✅ 支持无 Session 的单次请求模式
-   ✅ 支持请求失败自动重试（可配置重试次数与间隔）
-   ✅ 支持统一配置默认请求头和请求超时
-   ✅ 返回统一的字典格式结果，包含成功标志、状态码、响应数据或错误信息
-   ✅ 自动识别 JSON 响应并解析为 Python 对象
-   ✅ 支持 URL 自动拼接基础地址

### 1.2 📦 依赖安装

```bash
pip install requests
```

### 1.3 📁 文件结构说明

| 类/函数             | 说明                          |
| ---------------- | --------------------------- |
| `SyncHttpClient` | 同步 HTTP 请求客户端类封装，支持会话和单请求模式 |
| `get`            | 发起 GET 请求                   |
| `post`           | 发起 POST 请求                  |
| `put`            | 发起 PUT 请求                   |
| `delete`         | 发起 DELETE 请求                |
| `close`          | 关闭会话（如果启用了 Session）         |

### 1.4 🚀 快速使用

```python
from request_sync import SyncHttpClient

client = SyncHttpClient(
    base_url="https://api.example.com",
    default_headers={"User-Agent": "MyApp/1.0"},
    timeout=10,
    retry=2,
    retry_delay=0.5,
    use_session=True,  # 是否启用会话模式
)

# GET 请求示例
resp = client.get("/users", params={"page": 1})
if resp["success"]:
    print("用户列表:", resp["data"])
else:
    print("请求失败:", resp["error"])

# POST 请求示例
resp = client.post("/users", json={"name": "Alice"})
print(resp)

# 关闭会话
client.close()
```

### 1.5 `SyncHttpClient` 参数说明

| 参数名               | 类型               | 说明                                      |
| ----------------- | ---------------- | --------------------------------------- |
| `base_url`        | `str`            | 基础请求地址，所有请求 URL 自动拼接此地址                 |
| `default_headers` | `Dict[str, str]` | 默认请求头，所有请求都会带上，支持覆盖                     |
| `timeout`         | `int`            | 请求超时时间（秒），默认 10 秒                       |
| `retry`           | `int`            | 请求失败时重试次数，默认 2 次                        |
| `retry_delay`     | `float`          | 重试间隔秒数，默认 0.5 秒                         |
| `use_session`     | `bool`           | 是否启用 `requests.Session`，启用后保持会话，默认 True |

### 1.6 📎 返回结果结构说明

所有请求方法返回一个字典，示例：

```python
{
    "success": True,                   # 请求是否成功（状态码 200-299）
    "status_code": 200,               # HTTP 响应状态码
    "data": {...} or "raw text",      # JSON 格式响应时为解析后的 Python 对象，否则为文本内容
}
```

请求失败时返回示例：

```python
{
    "success": False,
    "status_code": 404,       # 如果无法获取状态码则为 None
    "error": "错误描述信息"
}
```

### 1.7 📎 注意事项

-   默认启用 Session 模式，适合需要维护 Cookie 的场景；如果不需要，可以关闭 use_session 参数。
-   重试机制针对请求异常（网络错误、超时、HTTP错误等）生效。
-   JSON 响应的 Content-Type 需包含 application/json，否则返回原始文本。
-   日志通过 logging 记录请求失败信息，可根据需求配置日志级别与处理器。
-   关闭客户端时调用 close() 方法释放 Session 资源。

---

## 2. [异步HTTP客户端](request_async.py)

[`request_async.py`](request_async.py) 是一个基于 `httpx.AsyncClient` 的异步 HTTP 请求封装模块，适用于 FastAPI、异步爬虫、异步任务等场景，支持会话复用、自动重试、统一返回格式等特性。

### 2.1 ⚙️ 主要功能

-   ✅ 使用 httpx.AsyncClient 实现异步请求
-   ✅ 支持基于会话的连接复用，也可按需关闭
-   ✅ 自动重试机制（自定义重试次数与延迟）
-   ✅ 支持 GET / POST / PUT / DELETE 请求
-   ✅ 自动识别 JSON 响应格式并解析
-   ✅ 所有请求结果统一为标准字典结构
-   ✅ 与 asyncio 协同运行

### 2.2 📦 安装依赖

```bash
pip install httpx
```

### 2.3 📁 文件结构说明

| 类/函数              | 说明                   |
| ----------------- | -------------------- |
| `AsyncHttpClient` | 异步 HTTP 请求客户端封装类     |
| `get`             | 异步 GET 请求            |
| `post`            | 异步 POST 请求           |
| `put`             | 异步 PUT 请求            |
| `delete`          | 异步 DELETE 请求         |
| `close`           | 关闭会话连接（如启用了 Session） |

### 2.4 🚀 快速使用

```python
import asyncio
from request_async import AsyncHttpClient

async def main():
    client = AsyncHttpClient(
        base_url="https://api.example.com",
        default_headers={"Authorization": "Bearer token"},
        timeout=10,
        retry=2,
        retry_delay=0.5,
        use_session=True
    )

    # 发起异步 GET 请求
    resp = await client.get("/info", params={"q": "demo"})
    if resp["success"]:
        print("查询结果:", resp["data"])
    else:
        print("请求失败:", resp["error"])

    # 发起异步 POST 请求
    resp = await client.post("/submit", json={"name": "Bob"})
    print(resp)

    await client.close()

asyncio.run(main())
```

### 2.5 `AsyncHttpClient` 参数说明

| 参数名               | 类型               | 说明                           |
| ----------------- | ---------------- | ---------------------------- |
| `base_url`        | `str`            | 请求基础地址，所有 URL 相对路径自动拼接此前缀    |
| `default_headers` | `Dict[str, str]` | 默认请求头，每次请求会合并添加              |
| `timeout`         | `int`            | 请求超时（单位秒），默认 10 秒            |
| `retry`           | `int`            | 请求失败时自动重试次数，默认 2 次           |
| `retry_delay`     | `float`          | 每次重试之间的延迟秒数，默认 0.5 秒         |
| `use_session`     | `bool`           | 是否启用会话连接复用，默认 True（推荐开启提高性能） |

### 2.6 📎 返回结果结构说明

每个请求方法均返回如下结构的字典：

-   请求成功：

```bash
{
    "success": True,
    "status_code": 200,
    "data": {...}  # JSON 响应内容，或文本内容
}
```

-   请求失败：

```bash
{
    "success": False,
    "status_code": None,
    "error": "连接超时或其他异常信息"
}
```

### 2.7 📎 注意事项

-   `httpx.AsyncClient` 默认连接池和 Cookie 复用，建议开启 `use_session=True`；
-   若 `use_session=False`，则每次请求新建连接，适合临时或轻量请求；
-   异步函数必须运行在 asyncio 协程环境下，如 `asyncio.run(...)`；
-   自动重试机制适用于网络类异常，如超时、连接失败等；
-   JSON 自动解析依赖于响应头中 `Content-Type: application/json`，否则返回文本内容；
-   调用 `client.close()` 可释放资源，建议在程序结束前关闭连接。

---
