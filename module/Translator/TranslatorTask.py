import re
import time
import itertools

import rapidjson as json
from rich import box
from rich.table import Table

from base.Base import Base
from module.Cache.CacheItem import CacheItem
from module.Check.ResponseChecker import ResponseChecker
from module.CodeSaver import CodeSaver
from module.TextHelper import TextHelper
from module.Translator.TranslatorRequester import TranslatorRequester
from module.PromptBuilder import PromptBuilder
from module.NormalizeHelper import NormalizeHelper
from module.PunctuationHelper import PunctuationHelper

class TranslatorTask(Base):

    def __init__(self, config: dict, platform: dict, items: list[CacheItem]) -> None:
        super().__init__()

        # 初始化
        self.items = items
        self.config = config
        self.platform = platform
        self.code_saver = CodeSaver(self.config)
        self.response_checker = ResponseChecker(self.config)

        # 生成原文文本字典
        self.src_dict, self.sub_line_mapping_dict = self.generate_src_dict(items)

        # 正规化
        self.src_dict = self.normalize(self.src_dict)

        # 译前替换
        self.src_dict = self.replace_before_translation(self.src_dict)

        # 代码救星预处理
        self.src_dict = self.code_saver.preprocess(self.src_dict)

        # 生成请求提示词
        if self.platform.get("api_format") != "SakuraLLM":
            self.messages, self.extra_log = self.generate_prompt(self.src_dict)
        else:
            self.messages, self.extra_log = self.generate_prompt_sakura(self.src_dict)

    # 启动任务
    def start(self) -> dict:
        return self.request(self.src_dict)

    # 请求
    def request(self, src_dict: dict[str, str]) -> dict:
        # 任务开始的时间
        task_start_time = time.time()

        # 检测是否需要停止任务
        if Base.work_status == Base.Status.STOPING:
            return {}

        # 检查是否超时，超时则直接跳过当前任务，以避免死循环
        if time.time() - task_start_time >= self.config.get("request_timeout"):
            return {}

        # 发起请求
        requester = TranslatorRequester(self.config, self.platform)
        skip, response_think, response_result, prompt_tokens, completion_tokens = requester.request(self.messages)

        # 如果请求结果标记为 skip，即有错误发生，则跳过本次循环
        if skip == True:
            return {
                "check_flag": ResponseChecker.Error.UNKNOWN,
                "row_count": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
            }

        # 提取回复内容
        dst_dict: dict = TextHelper.safe_load_json_dict(response_result)

        # 检查回复内容
        check_flag = self.response_checker.check(src_dict, dst_dict)

        # 模型回复日志
        if response_think != "":
            self.extra_log.append("模型思考内容：\n" + response_think)
        if self.is_debug():
            self.extra_log.append("模型回复内容：\n" + response_result)

        # 检查译文
        if check_flag != None:
            # 打印任务结果
            self.print(
                self.generate_log_table(
                    *self.generate_log_rows(
                        f"译文文本未通过检查，将在下一轮次的翻译中自动重试 - {check_flag}",
                        task_start_time,
                        prompt_tokens,
                        completion_tokens,
                        [line.strip() for line in src_dict.values()],
                        [line.strip() for line in dst_dict.values()],
                        self.extra_log,
                    )
                )
            )
        else:
            # 标点修复
            dst_dict: dict[str, str] = self.punctuation_fix(src_dict, dst_dict)

            # 代码救星后处理
            dst_dict = self.code_saver.postprocess(dst_dict)

            # 译后替换
            dst_dict = self.replace_after_translation(dst_dict)

            # 拼接子句
            merged_dict = {}
            for k, v in dst_dict.items():
                i = self.sub_line_mapping_dict[k]
                merged_dict[i] = merged_dict.get(i, "") + v

            # 更新缓存数据
            for i, item in enumerate(self.items):
                item.set_dst(merged_dict.get(str(i), ""))
                item.set_status(Base.TranslationStatus.TRANSLATED)

            # 打印任务结果
            self.print(
                self.generate_log_table(
                    *self.generate_log_rows(
                        "",
                        task_start_time,
                        prompt_tokens,
                        completion_tokens,
                        [line.strip() for line in src_dict.values()],
                        [line.strip() for line in dst_dict.values()],
                        self.extra_log,
                    )
                )
            )

        # 返回任务结果
        if check_flag != None:
            return {
                "check_flag": check_flag,
                "row_count": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
            }
        else:
            return {
                "check_flag": None,
                "row_count": len(self.items),
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
            }

    # 正规化
    def normalize(self, data: dict[str, str]) -> dict:
        for k in data.keys():
            data[k] = NormalizeHelper.normalize(data.get(k, ""))

        return data

    # 译前替换
    def replace_before_translation(self, data: dict[str, str]) -> dict:
        if self.config.get("replace_before_translation_enable") == False:
            return data

        replace_dict: list[dict] = self.config.get("replace_before_translation_data")
        for k in data:
            for v in replace_dict:
                if v.get("src", "") in data[k]:
                    data[k] = data[k].replace(v.get("src", ""), v.get("dst", ""))

        return data

    # 译后替换
    def replace_after_translation(self, data: dict[str, str]) -> dict:
        if self.config.get("replace_after_translation_enable") == False:
            return data

        replace_dict: list[dict] = self.config.get("replace_after_translation_data")
        for k in data:
            for v in replace_dict:
                if v.get("src", "") in data[k]:
                    data[k] = data[k].replace(v.get("src", ""), v.get("dst", ""))

        return data

    # 标点修复
    def punctuation_fix(self, src_dict: dict[str, str], dst_dict: dict[str, str]) -> dict:
        for k in dst_dict:
            dst_dict[k] = PunctuationHelper.check_and_replace(src_dict[k], dst_dict[k])

        return dst_dict

    # 生成源字典
    def generate_src_dict(self, items: list[CacheItem]) -> tuple[dict, dict]:
        i = 0
        src_dict = {}
        sub_line_mapping_dict = {}
        for k, item in enumerate(items):
            for line in re.findall(r"(?:.+\n|.+$)", item.get_src()):
                src_dict[str(i)] = line
                sub_line_mapping_dict[str(i)] = str(k)
                i = i + 1

        return src_dict, sub_line_mapping_dict

    # 生成提示词
    def generate_prompt(self, src_dict: dict) -> tuple[list[dict], list[str]]:
        # 初始化
        messages = []
        extra_log = []

        # 基础提示词
        base = PromptBuilder.build_base(self.config, custom = self.config.get("custom_prompt_enable"))

        # 术语表
        if self.config.get("glossary_enable") == True:
            result = PromptBuilder.build_glossary(self.config, src_dict)
            if result != "":
                base = base + "\n" + result
                extra_log.append(result)

        # 构建提示词列表
        messages.append({
            "role": "user",
            "content": (
                f"{base}"
                + "\n" + "原文文本："
                + "\n" + json.dumps(src_dict, indent = None, ensure_ascii = False)
            ),
        })

        # 当目标为 google 系列接口时，转换 messages 的格式
        if self.platform.get("api_format") == "Google":
            new = []
            for m in messages:
                new.append({
                    "role": "model" if m.get("role") == "assistant" else m.get("role"),
                    "parts": m.get("content", ""),
                })
            messages = new

        return messages, extra_log

    # 生成提示词 - Sakura
    def generate_prompt_sakura(self, src_dict: dict) -> tuple[list[dict], list[str]]:
        # 初始化
        messages = []
        extra_log = []

        # 构建系统提示词
        messages.append({
            "role": "system",
            "content": "你是一个轻小说翻译模型，可以流畅通顺地以日本轻小说的风格将日文翻译成简体中文，并联系上下文正确使用人称代词，不擅自添加原文中没有的代词。"
        })

        # 术语表
        base = ""
        if self.config.get("glossary_enable") == True:
            result = PromptBuilder.build_glossary_sakura(self.config, src_dict)
            if result == "":
                base = "将下面的日文文本翻译成中文：\n" + "\n".join(src_dict.values())
            else:
                base = (
                    "根据以下术语表（可以为空）：\n" + result
                    + "\n" + "将下面的日文文本根据对应关系和备注翻译成中文：\n" + "\n".join(src_dict.values())
                )
                extra_log.append(result)

        # 构建提示词列表
        messages.append({
            "role": "user",
            "content": base,
        })

        return messages, extra_log

    # 生成日志行
    def generate_log_rows(self, error: str, start_time: int, prompt_tokens: int, completion_tokens: int, source: list[str], translated: list[str], extra_log: list[str]) -> tuple[list[str], bool]:
        rows = []

        if error != "":
            rows.append(error)
        else:
            rows.append(
                f"任务耗时 {(time.time() - start_time):.2f} 秒，"
                + f"文本行数 {len(source)} 行，提示词消耗 {prompt_tokens} Tokens，文本补全消耗 {completion_tokens} Tokens"
            )

        # 添加额外日志
        for v in extra_log:
            rows.append(v.strip())

        # 原文译文对比
        pair = ""
        for source, translated in itertools.zip_longest(source, translated, fillvalue = ""):
            pair = pair + "\n" + f"{source} [bright_blue]-->[/] {translated}"
        rows.append(pair.strip())

        return rows, error == ""

    # 生成日志表格
    def generate_log_table(self, rows: list, success: bool) -> Table:
        table = Table(
            box = box.ASCII2,
            expand = True,
            title = " ",
            caption = " ",
            highlight = True,
            show_lines = True,
            show_header = False,
            show_footer = False,
            collapse_padding = True,
            border_style = "green" if success else "red",
        )
        table.add_column("", style = "white", ratio = 1, overflow = "fold")

        for row in rows:
            if isinstance(row, str):
                table.add_row(row)
            else:
                table.add_row(*row)

        return table