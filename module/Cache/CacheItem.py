import threading

import tiktoken

from base.Base import Base
from base.BaseData import BaseData

class CacheItem(BaseData):

    class FileType():

        TXT: str = "TXT"
        TPP: str = "TPP"
        MTOOL: str = "MTOOL"


    def __init__(self, args: dict) -> None:
        super().__init__()

        # 默认值
        self.src: str = ""                                              # 原文
        self.dst: str = ""                                              # 译文
        self.row: int = 0                                               # 在原始文件中的行号
        self.file_type: str = ""                                        # 原始文件的类型
        self.file_path: str = ""                                        # 原始文件的相对路径
        self.status: str = Base.TranslationStatus.UNTRANSLATED          # 翻译状态

        # 初始化
        for k, v in args.items():
            setattr(self, k, v)

        # 线程锁
        self.lock = threading.Lock()

        # 类变量
        CacheItem.cache = CacheItem.cache if hasattr(CacheItem, "cache") else {}

    # 获取原文
    def get_src(self) -> str:
        with self.lock:
            return self.src

    # 设置原文
    def set_src(self, src: str) -> None:
        with self.lock:
            self.src = src

    # 获取译文
    def get_dst(self) -> str:
        with self.lock:
            return self.dst

    # 设置译文
    def set_dst(self, dst: str) -> None:
        with self.lock:
            # 有时候模型的回复反序列化以后会是 int 等非字符类型，所以这里要强制转换成字符串
            # TODO:可能需要更好的处理方式
            if isinstance(dst, str):
                self.dst = dst
            else:
                self.dst = str(dst)

    # 获取行号
    def get_row(self) -> int:
        with self.lock:
            return self.row

    # 设置行号
    def set_row(self, row: int) -> None:
        with self.lock:
            self.row = row

    # 获取文件类型
    def get_file_type(self) -> str:
        with self.lock:
            return self.file_type

    # 设置文件类型
    def set_file_type(self, type: str) -> None:
        with self.lock:
            self.file_type = type

    # 获取文件路径
    def get_file_path(self) -> str:
        with self.lock:
            return self.file_path

    # 设置文件路径
    def set_file_path(self, path: str) -> None:
        with self.lock:
            self.file_path = path

    # 获取翻译状态
    def get_status(self) -> int:
        with self.lock:
            return self.status

    # 设置翻译状态
    def set_status(self, status: int) -> None:
        with self.lock:
            self.status = status

    # 获取 Token 数量
    def get_token_count(self) -> int:
        with self.lock:
            if self.src not in CacheItem.cache:
                CacheItem.cache[self.src] = len(
                    tiktoken.get_encoding("cl100k_base").encode(self.src)
                )

            return CacheItem.cache[self.src]