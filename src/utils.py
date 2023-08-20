from typing import Callable, List
from dataclasses import dataclass
import yaml
import os

from src.exceptions import *


# class for use dict as javascript
# example:
# response.data[0].name.text
class Struct(dict):
    __setattr__ = dict.__setitem__

    def __gelattr__(self, key):
        super().__delitem__(key)
        object.__delattr__(self, key)

    def __getattr__(cls, key):
        item = cls.get(key)
        if isinstance(item, dict):
            item = Struct(**item)
        elif isinstance(item, list):
            for i in range(len(item)):
                if isinstance(item[i], dict):
                    item[i] = Struct(**item[i])
        return item

@dataclass
class Navigator:
    callback: Callable
    page: str
    buttons: List[int]

@dataclass
class InputHandler:
    callback: Callable
    on_page: str

@dataclass
class ViewPreparation:
    callback: Callable
    key: str

class LocalMemory(Struct): 
    pass

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
    RU_RIGHT = 'в'

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

def load_yaml(path):
    with open(path, 'r', encoding = 'utf-8') as f:
        return Struct(**yaml.safe_load(f))

def nth_repl(s, sub, repl, n):
    """https://stackoverflow.com/questions/35091557/replace-nth-occurrence-of-substring-in-string"""
    find = s.find(sub)
    # If find is not -1 we have found at least one match for the substring
    i = find != -1
    # loop util we find the nth or we find no match
    while find != -1 and i != n:
        # find + 1 means we start searching from after the last match
        find = s.find(sub, find + 1)
        i += 1
    # If i is equal to n we found nth match so replace
    if i == n:
        return s[:find] + repl + s[find+len(sub):]
    return s