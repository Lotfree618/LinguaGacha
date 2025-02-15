import rapidjson as json
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtCore import Qt
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import QLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QTableWidgetItem
from qfluentwidgets import Action
from qfluentwidgets import FluentIcon
from qfluentwidgets import MessageBox
from qfluentwidgets import TableWidget
from qfluentwidgets import FluentWindow
from qfluentwidgets import TransparentPushButton

from base.Base import Base
from module.TableHelper import TableHelper
from widget.CommandBarCard import CommandBarCard
from widget.SwitchButtonCard import SwitchButtonCard

class ReplaceBeforeTranslationPage(QWidget, Base):

    # 表格每列对应的数据字段
    KEYS = (
        "src",
        "dst",
    )

    def __init__(self, text: str, window: FluentWindow) -> None:
        super().__init__(parent = window)
        self.setObjectName(text.replace(" ", "-"))

        # 默认配置
        self.default = {
            "replace_before_translation_enable": True,
            "replace_before_translation_data": [
                {
                    "src": "\\n[1]",
                    "dst": "示例姓名"
                },
                {
                    "src": "\\nn[1]",
                    "dst": "示例昵称"
                }
            ],
        }

        # 载入并保存默认配置
        config = self.save_config(self.load_config_from_default())

        # 设置主容器
        self.container = QVBoxLayout(self)
        self.container.setSpacing(8)
        self.container.setContentsMargins(24, 24, 24, 24) # 左、上、右、下

        # 添加控件
        self.add_widget_head(self.container, config, window)
        self.add_widget_body(self.container, config, window)
        self.add_widget_foot(self.container, config, window)

    # 头部
    def add_widget_head(self, parent: QLayout, config: dict, window: FluentWindow) -> None:

        def init(widget: SwitchButtonCard) -> None:
            widget.set_checked(config.get("replace_before_translation_enable"))

        def checked_changed(widget: SwitchButtonCard, checked: bool) -> None:
            config = self.load_config()
            config["replace_before_translation_enable"] = checked
            self.save_config(config)

        parent.addWidget(
            SwitchButtonCard(
                "译前替换",
                (
                    "在翻译开始前，将原文中匹配的部分替换为指定的文本，执行的顺序为从上到下依次替换"
                    + "\n" + "翻译 RPGMaker MV/MZ 游戏时，导入 data 或 www\\data 文件夹内的 Actors.json 文件可以显著提升翻译质量"
                ),
                init = init,
                checked_changed = checked_changed,
            )
        )

    # 主体
    def add_widget_body(self, parent: QLayout, config: dict, window: FluentWindow) -> None:

        def item_changed(item: QTableWidgetItem) -> None:
            item.setTextAlignment(Qt.AlignCenter)

        self.table = TableWidget(self)
        parent.addWidget(self.table)

        # 设置表格属性
        self.table.setBorderRadius(4)
        self.table.setBorderVisible(True)
        self.table.setWordWrap(False)
        self.table.setColumnCount(len(ReplaceBeforeTranslationPage.KEYS))
        self.table.resizeRowsToContents() # 设置行高度自适应内容
        self.table.resizeColumnsToContents() # 设置列宽度自适应内容
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch) # 撑满宽度
        self.table.itemChanged.connect(item_changed)

        # 设置水平表头并隐藏垂直表头
        self.table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.table.setHorizontalHeaderLabels(
            [
                "原文",
                "替换",
            ],
        )

        # 向表格更新数据
        TableHelper.update_to_table(self.table, config.get("replace_before_translation_data"), ReplaceBeforeTranslationPage.KEYS)

    # 底部
    def add_widget_foot(self, parent: QLayout, config: dict, window: FluentWindow) -> None:
        self.command_bar_card = CommandBarCard()
        parent.addWidget(self.command_bar_card)

        # 添加命令
        self.command_bar_card.set_minimum_width(512)
        self.add_command_bar_action_import(self.command_bar_card, config, window)
        self.add_command_bar_action_export(self.command_bar_card, config, window)
        self.command_bar_card.add_separator()
        self.add_command_bar_action_add(self.command_bar_card, config, window)
        self.add_command_bar_action_save(self.command_bar_card, config, window)
        self.command_bar_card.add_separator()
        self.add_command_bar_action_reset(self.command_bar_card, config, window)
        self.command_bar_card.add_stretch(1)
        self.add_command_bar_action_wiki(self.command_bar_card, config, window)

    # 导入
    def add_command_bar_action_import(self, parent: CommandBarCard, config: dict, window: FluentWindow) -> None:

        def triggered() -> None:
            # 选择文件
            path, _ = QFileDialog.getOpenFileName(None, "选择文件", "", "json 文件 (*.json);;xlsx 文件 (*.xlsx)")
            if not isinstance(path, str) or path == "":
                return

            # 从文件加载数据
            data = TableHelper.load_from_file(path, ReplaceBeforeTranslationPage.KEYS)

            # 读取配置文件
            config = self.load_config()
            config["replace_before_translation_data"].extend(data)

            # 向表格更新数据
            TableHelper.update_to_table(self.table, config["replace_before_translation_data"], ReplaceBeforeTranslationPage.KEYS)

            # 从表格加载数据（去重后）
            config["replace_before_translation_data"] = TableHelper.load_from_table(self.table, ReplaceBeforeTranslationPage.KEYS)

            # 保存配置文件
            config = self.save_config(config)

            # 弹出提示
            self.emit(Base.Event.TOAST_SHOW, {
                "type": Base.ToastType.SUCCESS,
                "message": "数据已导入 ...",
            })

        parent.add_action(
            Action(FluentIcon.DOWNLOAD, "导入", parent, triggered = triggered),
        )

    # 导出
    def add_command_bar_action_export(self, parent: CommandBarCard, config: dict, window: FluentWindow) -> None:

        def triggered() -> None:
            # 从表格加载数据
            data = TableHelper.load_from_table(self.table, ReplaceBeforeTranslationPage.KEYS)

            # 导出文件
            with open(f"导出_译前替换.json", "w", encoding = "utf-8") as writer:
                writer.write(json.dumps(data, indent = 4, ensure_ascii = False))

            # 弹出提示
            self.emit(Base.Event.TOAST_SHOW, {
                "type": Base.ToastType.SUCCESS,
                "message": "数据已导出到应用根目录 ...",
            })

        parent.add_action(
            Action(FluentIcon.SHARE, "导出", parent, triggered = triggered),
        )

    # 添加新行
    def add_command_bar_action_add(self, parent: CommandBarCard, config: dict, window: FluentWindow) -> None:

        def triggered() -> None:
            # 添加新行
            self.table.setRowCount(self.table.rowCount() + 1)

            # 弹出提示
            self.emit(Base.Event.TOAST_SHOW, {
                "type": Base.ToastType.SUCCESS,
                "message": "新行已添加 ...",
            })

        parent.add_action(
            Action(FluentIcon.ADD_TO, "添加", parent, triggered = triggered),
        )

    # 保存
    def add_command_bar_action_save(self, parent: CommandBarCard, config: dict, window: FluentWindow) -> None:

        def triggered() -> None:
            # 加载配置文件
            config = self.load_config()

            # 从表格加载数据
            config["replace_before_translation_data"] = TableHelper.load_from_table(self.table, ReplaceBeforeTranslationPage.KEYS)

            # 清空表格
            self.table.clearContents()

            # 向表格更新数据
            TableHelper.update_to_table(self.table, config["replace_before_translation_data"], ReplaceBeforeTranslationPage.KEYS)

            # 从表格加载数据（去重后）
            config["replace_before_translation_data"] = TableHelper.load_from_table(self.table, ReplaceBeforeTranslationPage.KEYS)

            # 保存配置文件
            config = self.save_config(config)

            # 弹出提示
            self.emit(Base.Event.TOAST_SHOW, {
                "type": Base.ToastType.SUCCESS,
                "message": "数据已保存 ...",
            })

        parent.add_action(
            Action(FluentIcon.SAVE, "保存", parent, triggered = triggered),
        )

    # 重置
    def add_command_bar_action_reset(self, parent: CommandBarCard, config: dict, window: FluentWindow) -> None:

        def triggered() -> None:
            message_box = MessageBox("警告", "是否确认重置为默认数据 ... ？", window)
            message_box.yesButton.setText("确认")
            message_box.cancelButton.setText("取消")

            if not message_box.exec():
                return

            # 清空表格
            self.table.clearContents()

            # 加载配置文件
            config = self.load_config()

            # 加载默认设置
            config["replace_before_translation_data"] = self.default.get("replace_before_translation_data")

            # 保存配置文件
            config = self.save_config(config)

            # 向表格更新数据
            TableHelper.update_to_table(self.table, config.get("replace_before_translation_data"), ReplaceBeforeTranslationPage.KEYS)

            # 弹出提示
            self.emit(Base.Event.TOAST_SHOW, {
                "type": Base.ToastType.SUCCESS,
                "message": "数据已重置 ...",
            })

        parent.add_action(
            Action(FluentIcon.DELETE, "重置", parent, triggered = triggered),
        )

    # WiKi
    def add_command_bar_action_wiki(self, parent: CommandBarCard, config: dict, window: FluentWindow) -> None:

        def connect() -> None:
            QDesktopServices.openUrl(QUrl("https://github.com/neavo/LinguaGacha/wiki"))

        push_button = TransparentPushButton(FluentIcon.HELP, "功能说明")
        push_button.clicked.connect(connect)
        parent.add_widget(push_button)