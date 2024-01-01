import logging
import datetime
import pathlib
import os
import time


def is_debug():
    return True


def get_datetime():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")


def parent(path):
    path = pathlib.Path(path)
    return str(path.parent)


def mkdir(path):
    pathlib.Path(path).mkdir(parents=True, exist_ok=True)


class LoggerContext:
    def __init__(self, lg, context):
        self.lg = lg
        self.context = context

    def __enter__(self):
        self.lg.push_context(self.context)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.lg.pop_context()


class LoggerProfile:
    def __init__(self, lg, profile, level="debug"):
        self.lg = lg
        self.profile = profile
        self.level = level

    def __enter__(self):
        if self.level == "debug":
            self.lg.debug(f"\x1b[40m[{self.profile}]\x1b[49m: start")
        elif self.level == "verbose":
            self.lg.verbose(f"\x1b[40m[{self.profile}]\x1b[49m: start")
        elif self.level == "log":
            self.lg.log(f"\x1b[40m[{self.profile}]\x1b[49m: start")
        elif self.level == "warn":
            self.lg.warn(f"\x1b[40m[{self.profile}]\x1b[49m: start")
        elif self.level == "error":
            self.lg.error(f"\x1b[40m[{self.profile}]\x1b[49m: start")
        self.lg.push_profile()

    def __exit__(self, exc_type, exc_val, exc_tb):
        t = self.lg.pop_profile()
        if self.level == "debug":
            self.lg.debug(f"\x1b[40m[{self.profile}]\x1b[49m: done: \x1b[31m{t} sec\x1b[0m")
        elif self.level == "verbose":
            self.lg.verbose(f"\x1b[40m[{self.profile}]\x1b[49m: done: \x1b[31m{t} sec\x1b[0m")
        elif self.level == "log":
            self.lg.log(f"\x1b[40m[{self.profile}]\x1b[49m: done: \x1b[31m{t} sec\x1b[0m")
        elif self.level == "warn":
            self.lg.warn(f"\x1b[40m[{self.profile}]\x1b[49m: done: \x1b[31m{t} sec\x1b[0m")
        elif self.level == "error":
            self.lg.error(f"\x1b[40m[{self.profile}]\x1b[49m: done: \x1b[31m{t} sec\x1b[0m")


class Logger:
    def __init__(self):
        self.lgs = []
        self.name = None
        self.contexts = ['']
        self.times = []
        self.pid = os.getpid()

    def set_name(self, name):
        self.name = name

    def push_context(self, context):
        self.contexts.append(context)

    def pop_context(self):
        self.contexts.pop()

    def context(self, context):
        return LoggerContext(self, context)

    def push_profile(self):
        self.times.append(time.time())

    def pop_profile(self):
        return round(time.time() - self.times.pop(), 3)

    def debug_profile(self, profile):
        return LoggerProfile(self, profile, "debug")

    def verbose_profile(self, profile):
        return LoggerProfile(self, profile, "verbose")

    def log_profile(self, profile):
        return LoggerProfile(self, profile, "log")

    def warn_profile(self, profile):
        return LoggerProfile(self, profile, "warn")

    def error_profile(self, profile):
        return LoggerProfile(self, profile, "error")

    def _format(self, msg: str, level: str, color: str, context: str, indent=0):
        return f"{color}[{self.name}] {self.pid} - \x1b[0m{get_datetime()} {color}{level:>7} {'| '*indent}\x1b[33m[{context}] {color}{msg}\x1b[0m"

    def add_console_logger(self, name, filter=logging.DEBUG):
        lg = logging.getLogger(name)
        lg.setLevel(filter)
        lg = self._clean_handler(lg)
        lg = self._add_console_handler(lg)
        self.lgs.append(lg)

    def add_file_logger(self, name, path, filter=logging.DEBUG):
        mkdir(parent(path))
        lg = logging.getLogger(name)
        lg.setLevel(filter)
        lg = self._clean_handler(lg)
        # lg = self._add_console_handler(lg)
        lg = self._add_file_handler(lg, path)
        self.lgs.append(lg)

    def _clean_handler(self, lg):
        lg.handlers = []
        return lg

    def _add_console_handler(self, lg):
        h = logging.StreamHandler()
        f = logging.Formatter("%(message)s")
        h.setFormatter(f)
        lg.addHandler(h)
        return lg

    def _add_file_handler(self, lg, path):
        h = logging.FileHandler(path)
        f = logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
        h.setFormatter(f)
        lg.addHandler(h)
        return lg

    def debug(self, msg, context=None):
        if is_debug():
            for lg in self.lgs:
                lg.debug(
                    self._format(msg, level="DEBUG", color="\x1b[35m", context=context or self.contexts[-1],
                                 indent=len(self.times)))

    def verbose(self, msg, context=None):
        for lg in self.lgs:
            lg.info(
                self._format(msg, level="VERBOSE", color="\x1b[36m", context=context or self.contexts[-1],
                             indent=len(self.times)))

    def log(self, msg, context=None):
        for lg in self.lgs:
            lg.info(
                self._format(msg, level="LOG", color="\x1b[32m", context=context or self.contexts[-1],
                             indent=len(self.times)))

    def warn(self, msg, context=None):
        for lg in self.lgs:
            lg.warning(
                self._format(msg, level="WARN", color="\x1b[33m", context=context or self.contexts[-1],
                             indent=len(self.times)))

    def error(self, msg, context=None):
        for lg in self.lgs:
            lg.error(
                self._format(msg, level="ERROR", color="\x1b[31m", context=context or self.contexts[-1],
                             indent=len(self.times)))


lg = Logger()
lg.add_console_logger("console", logging.DEBUG)
# ======================================================== #
# 사용 예시
# ======================================================== #
# lg.set_name("app name")
# lg.add_console_logger("console", logging.DEBUG)
# lg.add_file_logger("debug", f"./log/{get_datetime()}.debug.log", logging.DEBUG)
# lg.add_file_logger("info", f"./log/{get_datetime()}.info.log", logging.INFO)
# lg.add_file_logger("warn", f"./log/{get_datetime()}.warn.log", logging.WARN)
# lg.add_file_logger("error", f"./log/{get_datetime()}.error.log", logging.ERROR)

# with lg.context("main"):
#     lg.debug("debug")
#     lg.log("log")
#     lg.warn("warn")
#     lg.error("error")
#     with lg.log_profile("profile", "debug"):
#         lg.debug("debug")
#         lg.log("log")
#         lg.warn("warn")
#         lg.error("error")
#         with lg.log_profile("profile2", "debug"):
#             lg.debug("debug")
#             lg.debug("debug")
#             lg.debug("debug")
#             lg.debug("debug")
#             lg.log("log")
#             lg.warn("warn")
#             lg.error("error")
#         lg.debug("debug")
#         lg.log("log")
#         lg.warn("warn")
#         lg.error("error")
#     lg.debug("debug")
#     lg.log("log")
#     lg.warn("warn")
#     lg.error("error")

# lg.push_context("main")
# lg.debug("debug")
# lg.log("log")
# lg.warn("warn")
# lg.error("error")
# lg.pop_context()
