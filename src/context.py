import os
from typing import Any


from src.utils import Struct, LocalMemory, load_yaml
from src.exceptions import InvalidLanguageError
#from locale.config import *

class Localization(Struct):
    path = './locale'

    def __init__(self, language: str):
        self.language = language.upper()

        if self.language not in self.get_languages():
            raise InvalidLanguageError(f'Invalid language: {self.language}')
        
        data = load_yaml(f'{self.path}/{self.language.lower()}-{self.language.upper()}.yml')
        
        super().__init__(**data)

    def __getattr__(cls, key):
        res = super().__getattr__(key)

        if isinstance(res, str) and\
           res.strip().startswith('"') and\
           res.strip().endswith('"'):
            res = res.strip()[1:-1]

        return res


    @staticmethod
    def get_languages() -> list:
        files = os.listdir(Localization.path)

        langs = []

        for file in files:
            if (file.endswith('.yml') or file.endswith('.yaml')):
                lang = file.split('.')[0].split('-')[0]
                langs.append(lang.upper())

        return langs


class Context:
    @staticmethod
    def format_string(text: str, **kwargs) -> str:
        return text.format(**kwargs)

    def __init__(self):
        self.storage = Struct()
        self.temp_memory = LocalMemory()
        self.memory = LocalMemory()
        self.text = ''
    
    def clear_console(self) -> None:
        os.system('cls')

    def clear(self) -> None:
        self.storage.clear()
        self.text = ''

    def set_storage(self, **kwargs) -> None:
        self.storage.update(**kwargs)

    def set(self, text: str, **kwargs) -> None:
        self.text = text
        self.set_storage(**kwargs)

    def show(self, endless = False) -> str:
        text = Context.format_string(self.text, **self.storage)
        if text.strip().startswith('"') and\
           text.strip().endswith('"'):
            text = text.strip()[1:-1]
        print(text, end = '' if endless else '\n')

        return text
