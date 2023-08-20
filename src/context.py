import os


from src.utils import Struct, LocalMemory, load_yaml

class Localization(Struct):
    path = './locale'

    def __init__(self, language: str):
        self.language = language.upper()

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
            if 'all-ALL' in file: continue

            if (file.endswith('.yml') or file.endswith('.yaml')):
                lang = file.split('.')[0].split('-')[0]
                langs.append(Localization(lang))

        return langs
    
class Context:
    """
    Main Context class, store all info about current program state
    Like Model
    """

    @staticmethod
    def format_string(text: str, **kwargs) -> str:
        """Format string with kwargs"""
        return text.format(**kwargs)

    def __init__(self):
        self.storage = Struct()
        self.memory = LocalMemory()
        self.text = ''
    
    def clear_console(self) -> None:
        """Clear console"""
        os.system('cls')

    def clear(self) -> None:
        """Clear current text and storage"""
        self.storage.clear()
        self.text = ''

    def set_storage(self, **kwargs) -> None:
        """Add new values to storage"""
        self.storage.update(**kwargs)

    def set(self, text: str, **kwargs) -> None:
        """Set text and storage"""
        self.text = text
        self.set_storage(**kwargs)

    def show(self, endless = False) -> str:
        """Show page"""
        text = Context.format_string(self.text, **self.storage)
        if text.strip().startswith('"') and\
           text.strip().endswith('"'):
            text = text.strip()[1:-1]

        print(text, end = '' if endless else '\n')
        

        return text
