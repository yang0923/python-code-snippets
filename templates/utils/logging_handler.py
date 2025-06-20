# -*- coding: utf-8 -*-
#
# logging_handler.py
# @Date   : 2025/6/19 16:51:55
# @Author : yy
# @Des    : 多功能日志系统：支持彩色、多进程轮转、异常装饰器、标准 logging.config.dictConfig 兼容

import functools
import logging
import logging.config
import os
from typing import Union

from concurrent_log_handler import ConcurrentRotatingFileHandler


# =========================
# 彩色控制台处理器
# =========================
class ColoredConsoleHandler(logging.StreamHandler):
    COLORS = {
        "DEBUG": "\033[36m",
        "INFO": "\033[32m",
        "WARNING": "\033[33m",
        "ERROR": "\033[31m",
        "CRITICAL": "\033[35m",
        "DEBUG_MSG": "\033[36;2;3m",
        "INFO_MSG": "\033[32;2;3m",
        "WARNING_MSG": "\033[33;2;3m",
        "ERROR_MSG": "\033[31;2;3m",
        "CRITICAL_MSG": "\033[35;2;3m",
        "RESET": "\033[0m",
    }

    def emit(self, record):
        try:
            levelname = record.levelname
            msg = self.format(record)
            message = record.getMessage()
            level_part = msg.replace(message, "")

            color = self.COLORS.get(levelname, self.COLORS["RESET"])
            msg_color = self.COLORS.get(f"{levelname}_MSG", self.COLORS["RESET"])
            reset = self.COLORS["RESET"]

            formatted = f"{color}{level_part}{reset}{msg_color}{message}{reset}\n"
            self.stream.write(formatted)
            self.flush()
        except Exception:
            self.handleError(record)


class LoggerExtension:
    @staticmethod
    def catch(logger, level=logging.ERROR, reraise=True, on_error=None):
        """
        返回一个装饰器，用于捕获异常并记录日志
        :param logger: 日志记录器
        :param level: 日志级别
        :param reraise: 是否重新抛出异常
        :param on_error: 异常处理函数
        :return: 装饰器
        """

        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logger.log(
                        level,
                        f"函数 `{func.__name__}` 执行异常: {e}",
                        exc_info=True,
                        stacklevel=2,
                    )
                    if on_error:
                        on_error(e)
                    if reraise:
                        raise

            return wrapper

        return decorator

    @classmethod
    def monkey_patch(cls):
        """
        将 catch 注入到 logging.Logger
        """
        if not hasattr(logging.Logger, "catch"):

            def _catch(self, level=logging.ERROR, reraise=True, on_error=None):
                return cls.catch(self, level, reraise, on_error)

            logging.Logger.catch = _catch


class LogHandler(logging.Logger):
    """
    自定义日志器，支持彩色控制台、多进程安全文件轮转日志、错误日志拆分。

    参数:
    ----------
    name : str
        日志名称，通常为模块名或应用名，默认 "app"。

    log_path : str
        日志文件完整路径，支持带目录。默认 "logs/app.log"。

    level_console : int 或 str
        控制台日志输出级别。可用值有 "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL" 或对应数字。
        默认为 logging.INFO。

    level_file : int 或 str
        文件日志输出级别。默认为 logging.DEBUG。

    color_console : bool
        是否启用控制台彩色日志输出。默认 True。

    enable_console : bool
        是否启用控制台日志输出。默认 True。

    enable_file : bool
        是否启用文件日志输出。默认 True。

    detach_error : bool
        是否启用单独的错误日志文件（只记录 ERROR 及以上）。默认 True。

    file_max_bytes : int
        单个日志文件最大字节数，超过后自动轮转。默认 10 * 1024 * 1024 (10MB)。

    file_backup_count : int
        保留的日志备份文件数目。默认 5。

    fmt_console : str
        控制台日志输出格式字符串。默认 "[%(levelname)-8s] [%(name)s] [%(filename)s:%(funcName)s:%(lineno)d] - %(message)s"。

    fmt_file : str
        文件日志输出格式字符串。默认 "%(asctime)s - [%(levelname)-8s] [%(name)s] [%(filename)s:%(funcName)s:%(lineno)d] - %(message)s"。
    """

    def __init__(
        self,
        name: str = "app",
        log_path: str = "logs/app.log",
        level_console: Union[int, str] = logging.INFO,
        level_file: Union[int, str] = logging.DEBUG,
        color_console: bool = True,
        enable_console: bool = True,
        enable_file: bool = True,
        detach_error: bool = False,
        file_max_bytes: int = 10 * 1024 * 1024,
        file_backup_count: int = 5,
        fmt_console: str = "[%(levelname)-8s] [%(name)s] [%(filename)s:%(funcName)s:%(lineno)d] - %(message)s",
        fmt_file: str = "%(asctime)s - [%(levelname)-8s] [%(name)s] [%(filename)s:%(funcName)s:%(lineno)d] - %(message)s",
    ):
        super().__init__(name, min(level_console, level_file))
        LoggerExtension.monkey_patch()  # 安全注入 catch 方法
        self.log_path = os.path.abspath(log_path)
        self.level_console = level_console
        self.level_file = level_file
        self.color_console = color_console
        self.enable_console = enable_console
        self.enable_file = enable_file
        self.detach_error = detach_error
        self.file_max_bytes = file_max_bytes
        self.file_backup_count = file_backup_count
        self.fmt_console = fmt_console
        self.fmt_file = fmt_file

        log_dir = os.path.dirname(self.log_path)
        os.makedirs(log_dir, exist_ok=True)

        if self.enable_console:
            self._set_console_handler()
        if self.enable_file:
            self._set_file_handler()
            if self.detach_error:
                self._set_error_file_handler()

    def _set_console_handler(self):
        handler = (
            ColoredConsoleHandler() if self.color_console else logging.StreamHandler()
        )
        handler.setLevel(self.level_console)
        handler.setFormatter(logging.Formatter(self.fmt_console))
        self.addHandler(handler)

    def _set_file_handler(self):
        try:
            handler = ConcurrentRotatingFileHandler(
                filename=self.log_path,
                maxBytes=self.file_max_bytes,
                backupCount=self.file_backup_count,
                encoding="utf-8",
            )
            handler.setLevel(self.level_file)
            handler.setFormatter(logging.Formatter(self.fmt_file))
            if self.detach_error:
                # 只让小于 ERROR 级别的日志通过
                handler.addFilter(lambda record: record.levelno < logging.ERROR)
            self.addHandler(handler)
        except Exception as e:
            self.error(f"文件日志处理器初始化失败: {e}")

    def _set_error_file_handler(self):
        try:
            base, ext = os.path.splitext(self.log_path)
            error_path = f"{base}_error{ext or '.log'}"
            handler = ConcurrentRotatingFileHandler(
                filename=error_path,
                maxBytes=self.file_max_bytes,
                backupCount=self.file_backup_count,
                encoding="utf-8",
            )
            handler.setLevel(logging.ERROR)
            handler.setFormatter(logging.Formatter(self.fmt_file))
            self.addHandler(handler)
        except Exception as e:
            self.error(f"错误日志处理器初始化失败: {e}")


class AdvancedLogHandler(logging.Handler):
    """
    适用于各种 Python 项目的高级日志 Handler，
    支持多进程写入、彩色控制台、错误分离等功能。
    """

    _singleton_logger = None

    def __init__(
        self,
        name="app",
        log_path="logs/app.log",
        level_console="WARNING",
        level_file="DEBUG",
        detach_error=False,
        enable_console=True,
        enable_file=True,
        color_console=True,
        file_max_bytes=10 * 1024 * 1024,
        file_backup_count=5,
        fmt_console: str = "[%(levelname)-8s] [%(name)s] [%(filename)s:%(funcName)s:%(lineno)d] - %(message)s",
        fmt_file: str = "%(asctime)s - [%(levelname)-8s] [%(name)s] [%(filename)s:%(funcName)s:%(lineno)d] - %(message)s",
        **kwargs,
    ):
        super().__init__()
        self.setLevel(level_file)

        if not AdvancedLogHandler._singleton_logger:
            AdvancedLogHandler._singleton_logger = LogHandler(
                name=name,
                log_path=log_path,
                level_console=level_console,
                level_file=level_file,
                detach_error=detach_error,
                enable_console=enable_console,
                enable_file=enable_file,
                color_console=color_console,
                file_max_bytes=file_max_bytes,
                file_backup_count=file_backup_count,
                fmt_console=fmt_console,
                fmt_file=fmt_file,
            )
        self._logger = AdvancedLogHandler._singleton_logger

    def emit(self, record: logging.LogRecord):
        self._logger.handle(record)


if __name__ == "__main__":

    def test_loghandler():
        logger = LogHandler(
            name="test_logger",
            log_path="logs/test_app.log",
            level_console="DEBUG",
            level_file="DEBUG",
            detach_error=False,
            color_console=True,
            file_backup_count=5,
            file_max_bytes=1024 * 1024 * 10,
        )

        logger.debug("测试调试日志")
        logger.info("测试信息日志")
        logger.warning("测试警告日志")
        logger.error("测试错误日志")
        logger.critical("测试严重日志")

        # @logger.catch(level=logging.ERROR, reraise=False)
        # def background_task():
        #     raise ValueError("任务失败")

        # background_task()
        @logger.catch(level=logging.ERROR, reraise=False)
        def test_func():
            return 1 / 0

        test_func()

    def test_django_handler():
        handler = AdvancedLogHandler(
            name="test_django_logger",
            log_path="logs/test_django.log",
            level_console="DEBUG",
            level_file="DEBUG",
            detach_error=True,
            color_console=True,
            file_backup_count=5,
            file_max_bytes=1024 * 1024 * 10,
        )
        logger = logging.getLogger("test_django_logger")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        logger.debug("DjangoCompatibleHandler 测试调试日志")
        logger.info("DjangoCompatibleHandler 测试信息日志")
        logger.warning("DjangoCompatibleHandler 测试警告日志")
        logger.error("DjangoCompatibleHandler 测试错误日志")
        logger.critical("DjangoCompatibleHandler 测试严重日志")

        @logger.catch(level=logging.ERROR, reraise=False)
        def background_task():
            raise ValueError("任务失败")

        background_task()

    def test_dict_logging():
        LOGGING_CONFIG = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "console_fmt": {
                    "format": "[%(asctime)s] %(levelname)s - %(message)s",
                },
                "file_fmt": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "advanced": {
                    "()": AdvancedLogHandler,  # 这里用类路径
                    "name": "dict_logger",
                    "log_path": "logs/dict_config.log",
                    "level_console": "DEBUG",
                    "level_file": "DEBUG",
                    "color_console": True,
                    "enable_console": True,
                    "enable_file": True,
                    "detach_error": True,
                    "file_max_bytes": 1024 * 1024 * 10,  # 1MB
                    "file_backup_count": 3,
                    "fmt_console": "[%(asctime)s] %(levelname)s - %(message)s",
                    "fmt_file": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                }
            },
            "loggers": {
                "dict_logger": {
                    "handlers": ["advanced"],
                    "level": "DEBUG",
                    "propagate": False,
                },
            },
        }

        logging.config.dictConfig(LOGGING_CONFIG)
        logger = logging.getLogger("dict_logger")

        logger.debug("这是 dictConfig 测试的调试日志")
        logger.info("这是 dictConfig 测试的信息日志")
        logger.warning("这是 dictConfig 测试的警告日志")
        logger.error("这是 dictConfig 测试的错误日志")
        logger.critical("这是 dictConfig 测试的严重日志")

        @logger.catch(level=logging.ERROR, reraise=False)
        def background_task():
            raise ValueError("任务失败")

        background_task()

    # 测试用例
    test_loghandler()
    # test_django_handler()
    # test_dict_logging()
