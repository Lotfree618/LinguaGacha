import itertools
import unicodedata

class NormalizeHelper():

    # 自定义规则
    CUSTOM_RULE = {}

    # 全角转半角
    CUSTOM_RULE.update({chr(i): chr(i - 0xFEE0) for i in itertools.chain(
        range(0xFF21, 0xFF3A + 1),   # 全角 A-Z 转换为 半角 A-Z
        range(0xFF41, 0xFF5A + 1),   # 全角 a-z 转换为 半角 a-z
        range(0xFF10, 0xFF19 + 1),   # 全角 0-9 转换为 半角 0-9
    )})

    # 全角转半角 - 片假名
    CUSTOM_RULE.update({
        "ｱ": "ア",
        "ｲ": "イ",
        "ｳ": "ウ",
        "ｴ": "エ",
        "ｵ": "オ",
        "ｶ": "カ",
        "ｷ": "キ",
        "ｸ": "ク",
        "ｹ": "ケ",
        "ｺ": "コ",
        "ｻ": "サ",
        "ｼ": "シ",
        "ｽ": "ス",
        "ｾ": "セ",
        "ｿ": "ソ",
        "ﾀ": "タ",
        "ﾁ": "チ",
        "ﾂ": "ツ",
        "ﾃ": "テ",
        "ﾄ": "ト",
        "ﾅ": "ナ",
        "ﾆ": "ニ",
        "ﾇ": "ヌ",
        "ﾈ": "ネ",
        "ﾉ": "ノ",
        "ﾊ": "ハ",
        "ﾋ": "ヒ",
        "ﾌ": "フ",
        "ﾍ": "ヘ",
        "ﾎ": "ホ",
        "ﾏ": "マ",
        "ﾐ": "ミ",
        "ﾑ": "ム",
        "ﾒ": "メ",
        "ﾓ": "モ",
        "ﾔ": "ヤ",
        "ﾕ": "ユ",
        "ﾖ": "ヨ",
        "ﾗ": "ラ",
        "ﾘ": "リ",
        "ﾙ": "ル",
        "ﾚ": "レ",
        "ﾛ": "ロ",
        "ﾜ": "ワ",
        "ｦ": "ヲ",
        "ﾝ": "ン",
        "ｧ": "ァ",
        "ｨ": "ィ",
        "ｩ": "ゥ",
        "ｪ": "ェ",
        "ｫ": "ォ",
        "ｬ": "ャ",
        "ｭ": "ュ",
        "ｮ": "ョ",
        "ｯ": "ッ",
        "ｰ": "ー",
        "ﾞ": "゛",  # 浊音符号
        "ﾟ": "゜",  # 半浊音符号
    })

    # 规范化
    def normalize(text: str) -> str:
        # NFC（Normalization Form C）：将字符分解后再合并成最小数量的单一字符（合成字符）。
        # NFD（Normalization Form D）：将字符分解成组合字符（即一个字母和附加的重音符号等）。
        # NFKC（Normalization Form KC）：除了合成与分解外，还会进行兼容性转换，例如将全角字符转换为半角字符。
        # NFKD（Normalization Form KD）：除了分解外，还会进行兼容性转换。
        text = unicodedata.normalize("NFC", text)

        # 应用自定义的规则
        text = "".join([NormalizeHelper.CUSTOM_RULE.get(char, char) for char in text])

        # 返回结果
        return text