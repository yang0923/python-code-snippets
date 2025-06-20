# 常用工具

-   [日志处理](#1-日志处理)

---

## 1. [日志处理](logging_handler.py)

[`logging_handler.py`](logging_handler.py) 是一个多功能日志系统封装模块，适用于各种 Python 项目（包括脚本、Django、FastAPI 等），具备以下功能：

-   ✅ 控制台彩色日志输出（可选）
-   ✅ 多进程安全的日志文件轮转（使用 `ConcurrentRotatingFileHandler`）
-   ✅ 错误日志文件分离（可选）
-   ✅ 函数异常自动捕获记录（通过装饰器）
-   ✅ 与 `logging.config.dictConfig` 完全兼容

### 1.1 📦 安装依赖

```bash
pip install concurrent-log-handler
```

### 1.2 📁 文件结构说明

| 类/函数                    | 说明                                |
| ----------------------- | --------------------------------- |
| `LogHandler`            | 日志核心类，封装控制台 + 文件日志输出              |
| `AdvancedLogHandler`    | 高级日志处理器，用于 Django 等标准配置集成         |
| `LoggerExtension.catch` | 捕获函数异常的装饰器                        |
| `test_loghandler()`     | 测试基础用法                            |
| `test_django_handler()` | 测试 Django 中的用法                    |
| `test_dict_logging()`   | 测试 logging.config.dictConfig 配置使用 |

### 1.3 🚀 快速使用

#### 1.3.1 方法1: 直接使用 `LogHandler`

```python
from logging_handler import LogHandler

logger = LogHandler(name="my_app", log_path="logs/my_app.log")

logger.debug("This is a debug message")
logger.info("This is an info message")
logger.warning("This is a warning message")
logger.error("This is an error message")
logger.critical("This is a critical message")

@logger.catch(level=logging.ERROR, reraise=False)
def test_func():
    return 1 / 0

test_func()

```

#### 1.3.2 方法2: 使用`AdvancedLogHandler`集成到 Django 或标准 dictConfig 配置

```python
from logging
from logging_handler import AdvancedLogHandler

LOGGING = {
    "version": 1,
    "handlers": {
        "default": {
            "()": AdvancedLogHandler,
            "name": "my_project",
            "log_path": "logs/project.log",
            "color_console": True,
            "detach_error": True,
        }
    },
    "loggers": {
        "django": {
            "handlers": ["default"],
            "level": "DEBUG",
            "propagate": False
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("dict_logger")

logger.debug("这是 dictConfig 测试的调试日志")
logger.info("这是 dictConfig 测试的信息日志")
logger.warning("这是 dictConfig 测试的警告日志")
logger.error("这是 dictConfig 测试的错误日志")
logger.critical("这是 dictConfig 测试的严重日志")

@logger.catch(level=logging.ERROR, reraise=False)
def test_func():
    return 1 / 0

test_func()

```

### 1.4 ⚙️ LogHandler 参数说明

| 参数名                 | 类型        | 说明                     |
| ------------------- | --------- | ---------------------- |
| `name`              | `str`     | 日志器名称                  |
| `log_path`          | `str`     | 日志文件路径                 |
| `level_console`     | `str/int` | 控制台日志级别，默认 `INFO`      |
| `level_file`        | `str/int` | 文件日志级别，默认 `DEBUG`      |
| `color_console`     | `bool`    | 控制台是否启用彩色输出            |
| `enable_console`    | `bool`    | 是否启用控制台输出              |
| `enable_file`       | `bool`    | 是否启用文件输出               |
| `detach_error`      | `bool`    | 是否将 ERROR 日志单独写入错误日志文件 |
| `file_max_bytes`    | `int`     | 日志文件轮转的最大字节数           |
| `file_backup_count` | `int`     | 日志文件保留数量               |
| `fmt_console`       | `str`     | 控制台日志格式                |
| `fmt_file`          | `str`     | 文件日志格式                 |

### 1.5 📎 注意事项

-   Windows 控制台默认不支持 ANSI 颜色输出，可使用兼容终端或关闭颜色；
-   确保日志目录存在或具有写入权限，程序会自动创建目录；
-   建议日志级别合理配置，避免输出过多无用信息影响性能。

---
