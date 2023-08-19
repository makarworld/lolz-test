from src.inputs import InputManager
from src.context import Localization, Context
from src.utils import (
    create_buttons, wait_key, set_console_size, 
    KeyMap, ControlKey, gui_handler,
    LocalMemory, Storage, State
)
import os 
import time
from loguru import logger


from src.models import Game

set_console_size(70, 39)

class BaseModel:
    context = Context()
    
class GameModel(BaseModel):
    def __init__(self) -> None:
        # Заблокировать кнопки горизонтали и вертикали
        self.vertical_lock = True 
        self.horizontal_lock = True
        
        # Значение текущей выбранной кнопки
        self.current_button = 1
        # Значение текущей страницы
        self.current_page = 1
        # Текущее действие
        self.action = None 
        # список данных для ввода
        self.input_requests = []


    def set_context(self, *args, **kwargs):
        self.context.set(*args, **kwargs)

    def set_storage(self, **kwargs):
        self.context.set_storage(**kwargs)
    
    def set_memory(self, **kwargs):
        self.context.memory.update(**kwargs)
    
    def set_temp_memory(self, **kwargs):
        self.context.temp_memory.update(**kwargs)

class GameView(BaseModel):
    def show(self):
        self.context.show()

class GameController(BaseModel):
    def press_key(self, key):
        # Ивент нажатия на кнопку
        # Если пользователь нажал на кнопку то изменить параметры модели
        # Если действие не заблокировано
        # Если он нажал вниз/вверх то изменить текущий выбор
        # Если нажал влево вправо то изменить текущую страницу если это возможно
        # Если нажал ESC вернуться в меню
        # Если нажал на ENTER то выполнить действие
        pass

    def input_value(self, value):
        # Ивент ввода значения
        # Получить из модели последнее запрошенное значение
        # Если значение было запрошено и не было ошибки при вводе, то записать значение и поменять состояние на следующий запрос
        # Если была ошибка то записать её и вернуть ошибку
        pass

context = Context()
locale = Localization('ru')
context.set(locale.context_menu)
context.set_storage(
    banner = Context.format_string(locale.banner, 
                                   author = '@abuztrade',
                                   language = locale.language),
    control_term = locale.control_term,
    context = '',
)

@gui_handler(context = context,
    storage = Storage(),
    state = State(
        current_button = 1,
        last_key = '')
)
def main(context: Context):
    while True:
        context.clear_console()
        context.set_storage(
            header = locale.select_action.text,
            footer = create_buttons(
                locale.select_action.buttons, 
                indent = 10,
                selected = context.memory.current_button
            )
        )

        # check if function returned from add_game()
        # if status - True add success message
        # if status - False add error message
        if context.memory.from_action:
            match context.memory.from_action:
                case "add_game":
                    if context.memory.from_action.status is True:
                        context.storage.context = Context.format_string(locale.add_action_success, 
                                                                        name = context.memory.game.name)
                    else:
                        context.storage.context = Context.format_string(locale.error, 
                                                                        error = context.memory.error)
            context.memory.from_action = None

        context.show()

        key = wait_key()

        arrow = last_key + key
        last_key = key

        if KeyMap.whatkey(key) == ControlKey.ENTER:
            if context.memory.current_button == 1:
                add_game()

        with open('key.txt', 'w', encoding='utf-8') as f:
            f.write(str(arrow.encode()))

        if KeyMap.whatkey(key, arrow) == ControlKey.UP:
            context.memory.current_button -= 1

        elif KeyMap.whatkey(key, arrow) == ControlKey.DOWN:
            context.memory.current_button += 1

        context.memory.current_button = min(max(context.memory.current_button, 1), len(locale.select_action.buttons))

@gui_handler(context = context,
    storage = Storage(
        header = locale.add_action_text
    ),
    temp_memory = LocalMemory(
        step = 1
    )
)
def add_game(context: Context):
    def on_error_input(value, err):
        if value != '-':
            context.memory.error = str(err)
            return
        else:
            return value

    while True:
        context.clear_console()

        match context.temp_memory.step:
            case 1:
                step_locale = locale.input_name
                value_type = str
                err_name = locale.errors_list.name
            case 2:
                step_locale = locale.input_author
                value_type = str
                err_name = locale.errors_list.author
            case 3:
                step_locale = locale.input_year
                value_type = int
                err_name = locale.errors_list.year

        context.set_storage(
            context = Context.format_string(locale.add_action_context,
                                            name   = context.temp_memory.get('name', '-'),
                                            author = context.temp_memory.get('author', '-'),
                                            year   = context.temp_memory.get('year', '-'),
                                            error  = context.temp_memory.get('error_year', '')),
            footer = step_locale
        )

        context.show(endless = True)

        value = InputManager.get_input(value_type, 
                                       on_error = on_error_input)
        
        # back to menu
        if value == '-':
            context.temp_memory.clear()
            context.set_storage(context = '')
            return

        if value:
            # write to memory
            match context.temp_memory.step:
                case 1:
                    context.temp_memory.update(name = value)
                case 2:
                    context.temp_memory.update(author = value)
                case 3:
                    context.temp_memory.update(year = value)
            context.temp_memory.step += 1
            context.temp_memory.error_year = ''
        else:
            context.temp_memory.error_year = Context.format_string(locale.error_add, 
                                                                   error_name = err_name)

        # if complite - save to database
        if context.temp_memory.step > 3:
            game = Game(
                name = context.temp_memory.name, 
                author = context.temp_memory.author, 
                year = context.temp_memory.year
            )
            game.save()
            context.memory.from_action = dict(
                status = True,
                action = 'add_game',
                name = context.temp_memory.name,
            )
            context.temp_memory.clear()
            context.set_storage(context = '')
            return
        
@gui_handler(context = context,
    storage = Storage(
        header = locale.find_game_action_text
    ),
    temp_memory = LocalMemory(
        step = 1
    )
)
def find_game(context: Context):
    def on_error_input(value, err):
        if value != '-':
            context.memory.error = str(err)
            return
        else:
            return value

    while True:
        context.clear_console()

        match context.temp_memory.step:
            case 1:
                step_locale = locale.input_name
                value_type = str
                err_name = locale.errors_list.name
            case 2:
                step_locale = locale.input_author
                value_type = str
                err_name = locale.errors_list.author
            case 3:
                step_locale = locale.input_year
                value_type = int
                err_name = locale.errors_list.year

        context.set_storage(
            context = Context.format_string(locale.add_action_context,
                                            name   = context.temp_memory.get('name', '-'),
                                            author = context.temp_memory.get('author', '-'),
                                            year   = context.temp_memory.get('year', '-'),
                                            error  = context.temp_memory.get('error_year', '')),
            footer = step_locale
        )

        context.show(endless = True)

        value = InputManager.get_input(value_type, 
                                       on_error = on_error_input)
        
        # back to menu
        if value == '-':
            context.temp_memory.clear()
            context.set_storage(context = '')
            return

        if value:
            # write to memory
            match context.temp_memory.step:
                case 1:
                    context.temp_memory.update(name = value)
                case 2:
                    context.temp_memory.update(author = value)
                case 3:
                    context.temp_memory.update(year = value)
            context.temp_memory.step += 1
            context.temp_memory.error_year = ''
        else:
            context.temp_memory.error_year = Context.format_string(locale.error_add, 
                                                                   error_name = err_name)

        # if complite - save to database
        if context.temp_memory.step > 3:
            game = Game(
                name = context.temp_memory.name, 
                author = context.temp_memory.author, 
                year = context.temp_memory.year
            )
            game.save()
            context.memory.from_action = dict(
                status = True,
                action = 'add_game',
                name = context.temp_memory.name,
            )
            context.temp_memory.clear()
            context.set_storage(context = '')
            return

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(e)
        input()
