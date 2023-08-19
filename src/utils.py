import os
import yaml

from src.exceptions import *
# class for use dict as javascript
# example:
# response.data[0].name.text
class Struct(dict):
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

    def __getattr__(cls, key):
        item = cls.get(key)
        if isinstance(item, dict):
            item = Struct(**item)
        elif isinstance(item, list):
            for i in range(len(item)):
                if isinstance(item[i], dict):
                    item[i] = Struct(**item[i])
        return item

class LocalMemory(Struct): 
    pass

class Storage(Struct):
    pass

class State(Struct):
    pass

def error_handler(except_type: Exception):
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                raise except_type(e)
        return wrapper
    return decorator

def gui_handler(context, text: str, storage: Storage, memory: LocalMemory, temp_memory: LocalMemory):
    # TODO: Доделать чтобы это был декоратор типо
    # @gui_page(text = locale.text, banner = locale.banner, footer = locale.footer)
    def decorator(func):
        def wrapper(*args, **kwargs):

            context.set(text)
            context.set_storage(**storage)
            context.memory.update(**memory)
            context.temp_memory.clear()
            context.temp_memory.update(**temp_memory)

            return func(context = context, *args, **kwargs)

        return wrapper
    return decorator

class GameAction:
    MENU = 0
    ADD_GAME = 1
    FIND_GAME = 2
    EDIT_GAME = 3
    DELETE_GAME = 4

def wait_key():
    ''' Wait for a key press on the console and return it. '''
    result = None
    if os.name == 'nt':
        import msvcrt
        result = msvcrt.getwch()
    else:
        import termios
        fd = sys.stdin.fileno()

        oldterm = termios.tcgetattr(fd)
        newattr = termios.tcgetattr(fd)
        newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, newattr)

        try:
            result = sys.stdin.read(1)
        except IOError:
            pass
        finally:
            termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)

    return result

class Key:
    UP = 'w'
    DOWN = 's'
    LEFT = 'a'
    RIGHT = 'd'

    RU_UP = 'ц'
    RU_DOWN = 'ы'
    RU_LEFT = 'ф'
    RU_RIGHT = 'ы'

    ENTER = '\r'
    ESC = ''

    ARROW_UP = b'\xc3\xa0H' 
    ARROW_DOWN = b'\xc3\xa0P'
    ARROW_LEFT = b'\xc3\xa0K'
    ARROW_RIGHT = b'\xc3\xa0M'

class ControlKey:
    UP = 'up'
    DOWN = 'down'
    LEFT = 'left'
    RIGHT = 'right'

    ENTER = 'enter'
    ESC = 'esc'
    UNKNOW = False

class KeyMap:
    UP = (Key.UP, Key.RU_UP, Key.ARROW_UP)
    DOWN = (Key.DOWN, Key.RU_DOWN, Key.ARROW_DOWN)
    LEFT = (Key.LEFT, Key.RU_LEFT, Key.ARROW_LEFT)
    RIGHT = (Key.RIGHT, Key.RU_RIGHT, Key.ARROW_RIGHT)

    @staticmethod
    def whatkey(key: str, arrow: bytes = b'') -> ControlKey:
        if key.lower() in KeyMap.UP or\
           arrow == KeyMap.UP[-1]:
            return ControlKey.UP
        
        elif key.lower() in KeyMap.DOWN or\
             arrow == KeyMap.DOWN[-1]:
            return ControlKey.DOWN
        
        elif key.lower() in KeyMap.LEFT or\
             arrow == KeyMap.LEFT[-1]:
            return ControlKey.LEFT
        
        elif key.lower() in KeyMap.RIGHT or\
             arrow == KeyMap.RIGHT[-1]:
            return ControlKey.RIGHT
        
        elif key == Key.ENTER:
            return ControlKey.ENTER
        
        elif key == Key.ESC:
            return ControlKey.ESC
        
        else:
            return ControlKey.UNKNOW


def set_console_size(width: int, height: int):
    os.system(f'cmd /c mode con: cols={width} lines={height}')

@error_handler(ReadYamlError)
def load_yaml(path):
    with open(path, 'r', encoding = 'utf-8') as f:
        return Struct(**yaml.safe_load(f))

def create_buttons(buttons: list, indent: int = 4, selected: int = 1, select_text = '[>] ') -> str:
    text = ""
    for i, b in enumerate(buttons):
        text += f"{select_text.rjust(indent) if i + 1 == selected else indent * ' '}{i + 1}. {b}\n"
    return text[:-1]