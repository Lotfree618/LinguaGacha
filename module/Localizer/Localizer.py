from base.Base import Base
from module.Localizer.LocalizerZH import LocalizerZH
from module.Localizer.LocalizerEN import LocalizerEN
from module.Localizer.LocalizerBase import LocalizerBase

class Localizer():

    def set_app_language(app_language: str) -> None:
        Localizer.app_language = app_language

    def get() -> LocalizerBase:
        if Localizer.app_language == Base.Language.EN:
            return LocalizerEN
        else:
            return LocalizerZH