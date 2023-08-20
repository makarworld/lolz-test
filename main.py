from src.inputs import InputManager
from src.context import Localization, Context
from src.utils import (
    create_buttons, wait_key, set_console_size, 
    KeyMap, ControlKey, gui_handler,
    LocalMemory, ViewPreparation, InputHandler, nth_repl, Navigator
)
from src.exceptions import *
from loguru import logger
from typing import Any, List, Callable

from src.models import Game

set_console_size(70, 39)

class ContextStorage:
    def __new__(cls, *args, **kwargs):
        it = cls.__dict__.get('__it__')
        if it is not None:
            return it 
        cls.__it__ = it = object.__new__(cls)
        it.init(*args, **kwargs)
        return it
    
    def init(self):
        self.context = Context()
        self.action = None

class GameModel:
    def __init__(self, cxt: ContextStorage) -> None:
        self.cxt = cxt

        # Значение текущей выбранной кнопки
        self.current_button = 1
        self.max_button = None

        # Значение текущей страницы
        self.current_page = 1
        self.max_page = None


    def clear_temp(self):
        try: self.cxt.context.memory.pop('name') 
        except: pass
        try: self.cxt.context.memory.pop('author') 
        except: pass
        try: self.cxt.context.memory.pop('year') 
        except: pass

class GameController:
    def __init__(self, cxt: ContextStorage, model: GameModel, locale: Localization):
        self.cxt = cxt
        self.model = model
        self.locale = locale
        self.last_key = ''
        self.navigators: List[Navigator] = []
        self.inputs_validators: List[InputHandler] = []

    # INPUT HANDLERS
    def register_inputs_validator(self, callback: Callable, on_page: str): 
        self.inputs_validators.append(
            InputHandler(
                callback = callback,
                on_page = on_page
            )
        )

    def call_inputs_validator(self): 
        for handler in self.inputs_validators:
            if (handler.on_page == self.cxt.action.name):
                return handler.callback(self)
            
        raise InputValidatorNotExist(f"Validator {self.cxt.action.name} not found")
    
    
    def input_validator(self, on_page: str): 
        def decorator(callback):
            self.register_inputs_validator(callback, on_page)

            return callback
        return decorator

    # NAVIGATORS
    def register_navigator(self, callback, page: str, buttons: List[int]):
        self.navigators.append(
            Navigator(
                callback = callback,
                page = page,
                buttons = buttons
            )
        )
    
    def call_navigator(self) -> None:
        for nav in self.navigators:
            if (nav.page == self.cxt.action.name) and\
               ((self.model.current_button in nav.buttons) or (not nav.buttons)):
                return nav.callback(self)
            
        raise PageNotExist(f"Page {self.cxt.action.name} with button {self.model.current_button} not found")
    
    def navigator(self, page_from: str, buttons: List[int]):
        def decorator(callback):
            self.register_navigator(callback, page_from, buttons)

            return callback
        return decorator

    def press_key(self, key: str):
        arrow = (self.last_key + key).encode()
        self.last_key = key

        with open('key.txt', 'w', encoding='utf-8') as f:
            f.write(arrow.decode() + '\n')
            f.write(key)

        if self.cxt.action.selectable:
            if KeyMap.whatkey(key, arrow) == ControlKey.UP:
                self.model.current_button -= 1

            elif KeyMap.whatkey(key, arrow) == ControlKey.DOWN:
                self.model.current_button += 1

            # limit to !> self.action.actions and !< 1
            self.model.current_button = max(1, min(self.model.max_button, self.model.current_button))

        if self.cxt.action.horizontal: 
            if KeyMap.whatkey(key, arrow) == ControlKey.LEFT:
                self.model.current_page -= 1

            elif KeyMap.whatkey(key, arrow) == ControlKey.RIGHT:
                self.model.current_page += 1

            # limit to !> self.action.actions and !< 1
            self.model.current_page = max(1, min(self.model.max_page, self.model.current_page))

        if KeyMap.whatkey(key) == ControlKey.ESC:
            self.set_action(self.locale.main)

        elif KeyMap.whatkey(key) == ControlKey.ENTER:
            self.call_navigator()


        # Ивент нажатия на кнопку
        # Если пользователь нажал на кнопку то изменить параметры модели
        # Если действие не заблокировано
        # Если он нажал вниз/вверх то изменить текущий выбор
        # Если нажал влево вправо то изменить текущую страницу если это возможно
        # Если нажал ESC вернуться в меню
        # Если нажал на ENTER то выполнить действие

    def input_value(self, value: Any, question: LocalMemory):

        if isinstance(value, tuple):
            if (value[0] != '' and question.nullable is False) and value[0] != '-':
                self.cxt.context.memory.error = question.error
                return
            
            elif value[0].strip() == '-':
                self.set_action(self.locale.main)
                return

            else:
                value = value[0]

        elif value == '-':
            self.set_action(self.locale.main)
            return
        
        elif not value and question.nullable is False:
            self.cxt.context.memory.error = question.error
            return
        
        # set value
        self.cxt.context.memory.update(**{question.name: value})
        self.cxt.context.memory.step += 1
        if self.cxt.context.memory.step >= len(self.cxt.action.questions):
            self.cxt.context.memory.step = 0
            self.call_inputs_validator()

        # Ивент ввода значения
        # Получить из модели последнее запрошенное значение
        # Если значение было запрошено и не было ошибки при вводе, то записать значение и поменять состояние на следующий запрос
        # Если была ошибка то записать её и вернуть ошибку

    def request(self):
        if self.cxt.action.input:
            question = self.cxt.action.questions[self.cxt.context.memory.step]
            match question.type:
                case 'int':
                    t = int
                case 'str':
                    t = str 

            value = InputManager.get_input(t, lambda v, err: (v, err))
            self.input_value(value, question)

        else:
            # ожидать нажатия клавиши
            key = wait_key()
            self.press_key(key)

    def set_action(self, locale: dict):
        # Сменить состояние
        self.model.clear_temp()
        self.model.current_button = 1
        self.model.current_page = 1
        self.cxt.context.memory.error = ''
        self.cxt.context.memory.step = 0

        if self.cxt.action and self.cxt.action.name == "main":
            self.cxt.context.storage.status = ''

        self.cxt.action = locale
        if self.cxt.action.selectable and self.cxt.action.actions:
            self.model.max_button = self.cxt.action.actions

        self.cxt.context.set(locale.text)

class GameView:
    def __init__(self, cxt: ContextStorage, model: GameModel, controller: GameController, locale: Localization):
        self.cxt = cxt
        self.model = model
        self.controller = controller
        self.locale = locale
        self.preparation_handlers: List[ViewPreparation] = []

    def register_preparation(self, callback: Callable, key: str): 
        self.preparation_handlers.append(
            ViewPreparation(
                callback = callback,
                key = key
            )
        )
    def call_preparation(self, key: str): 
        for preparation in self.preparation_handlers:
            if (preparation.key == key):
                return preparation.callback(self)
    
    def view_preparation(self, key: str): 
        def decorator(callback):
            self.register_preparation(callback, key)

            return callback
        return decorator


    def show(self):
        for key, value in self.cxt.action.items():
            if value:
                self.call_preparation(key)

        if self.cxt.action.selectable: 
            # replace selected button
            self.cxt.context.text = nth_repl(self.cxt.context.text, '{select}', '[>]', self.model.current_button)
            # replace other buttons
            self.cxt.context.text = self.cxt.context.text.replace('{select}', '   ',)
        
        if '{status}' in self.cxt.context.text:
            if not self.cxt.context.storage.get('status'):
                # set status after first start for avoid error
                self.cxt.context.storage['status'] = ''
            elif not '>>>' in self.cxt.context.storage['status']:
                self.cxt.context.storage['status'] = '>>> ' + self.cxt.context.storage['status']

        print(locale.banner)
        self.cxt.context.show(endless = self.cxt.action.input) # if input is true = endless mode

        # set previous text for clear all edits
        self.cxt.context.text = self.cxt.action.text 
    
    def clear(self):
        self.cxt.context.clear_console()

    def run_loop(self, first_page: Localization):
        controller.set_action(first_page)
        while True:
            view.show()
            controller.request()
            view.clear()

"""
TODO: 
Добавить бекспейс?
Запретить добавлять игры без названия и издателя
Добавить изменение игры
зарефакторить код, оптимизировать.
"""


locale = Localization('ru')

cxt = ContextStorage()
model = GameModel(cxt)
controller = GameController(cxt, model, locale)
view = GameView(cxt, model, controller, locale)

@controller.navigator(page_from = 'main', buttons = [1])
def add_game(controller: GameController):
    controller.set_action(controller.locale.add_game)

@controller.navigator(page_from = 'main', buttons = [2])
def find_game(controller: GameController):
    controller.set_action(controller.locale.find_game)

@controller.navigator(page_from = 'main', buttons = [3])
def game_list(controller: GameController):
    controller.set_action(controller.locale.game_list)
    controller.cxt.context.memory.games = list(Game.select())

@controller.navigator(page_from = 'game_list', buttons = []) # any button
def game_list_buttons(controller: GameController):
    game_index = (controller.cxt.action.rows * (controller.model.current_page - 1)) + controller.model.current_button - 1
    game: Game = controller.cxt.context.memory.games[game_index]
    controller.cxt.context.memory.current_game = game
    controller.cxt.context.set_storage(name = game.name, author = game.author, year = game.year)

    controller.set_action(controller.locale.game_page)

@controller.navigator(page_from = 'game_page', buttons = [1])
def game_page_edit(controller: GameController):
    controller.set_action(controller.locale.edit_game)

@controller.navigator(page_from = 'game_page', buttons = [2])
def game_page_delete(controller: GameController):
    controller.cxt.context.storage.status = controller.cxt.action.delete # delete
    game: Game = controller.cxt.context.memory.current_game
    game.delete_instance()
    controller.set_action(controller.locale.main) # to menu

@controller.navigator(page_from = 'game_page', buttons = [3])
def game_page_menu(controller: GameController):
    controller.set_action(controller.locale.game_list) # back

@controller.input_validator(on_page = "add_game")
def add_game_validator(controller: GameController):
    # Сохранить игру в бд
    game = Game(
        name = controller.cxt.context.memory.name, 
        author = controller.cxt.context.memory.author, 
        year = controller.cxt.context.memory.year)
    game.save()

    controller.cxt.context.storage.status = controller.cxt.action.success
    controller.set_action(controller.locale.main)

@controller.input_validator(on_page = "find_game")
def find_game_validator(controller: GameController):
    # если игры не найдены в статус поставить что нет таких и вернуть в меню
    # если найдены отправить на страницы с играми
    query = Game.select()

    if controller.cxt.context.memory.name:
        query = query.where(Game.name == controller.cxt.context.memory.name)
    if controller.cxt.context.memory.author:
        query = query.where(Game.author == controller.cxt.context.memory.author)
    if controller.cxt.context.memory.year:
        query = query.where(Game.year == controller.cxt.context.memory.year)
    
    result = list(query)
    if not result:
        controller.cxt.context.storage.status = controller.cxt.action.error
        controller.set_action(controller.locale.main)
        return
    else:
        controller.cxt.context.memory.games = result
        controller.set_action(controller.locale.game_list)

@view.view_preparation('horizontal')
def horizontal_view_preparation(view: GameView):
    max_page = len(view.cxt.context.memory.games) // view.cxt.action.rows + (1 if len(view.cxt.context.memory.games) % view.cxt.action.rows > 0 else 0)
    view.model.max_page = max_page
    view.cxt.context.set_storage(
        page = view.model.current_page,
        max_page = view.model.max_page,
        games = len(view.cxt.context.memory.games),
    )
    # build table
    page_games = view.cxt.context.memory.games[(view.model.current_page - 1) * view.cxt.action.rows:view.model.current_page * view.cxt.action.rows]
    view.model.max_button = len(page_games)
    i_length = len(view.cxt.action.headers[0]) + 2
    name_length = max([len(game.name) for game in page_games] + [len(view.cxt.action.headers[1])]) + 2
    author_length = max([len(game.author) for game in page_games] + [len(view.cxt.action.headers[2])]) + 2
    year_length = max([len(str(game.year)) for game in page_games] + [len(view.cxt.action.headers[3])]) + 2
    
    table_header = "|".join([
        view.cxt.action.headers[0].center(i_length),
        view.cxt.action.headers[1].center(name_length),
        view.cxt.action.headers[2].center(author_length),
        view.cxt.action.headers[3].center(year_length),
    ])
    rows = []
    for i, game in enumerate(page_games):
        row = "|".join([
            str((view.cxt.action.rows * (view.model.current_page - 1)) + (i + 1)).center(i_length),
            str(game.name).center(name_length),
            str(game.author).center(author_length),
            str(game.year).center(year_length),
        ])
        full_row = view.cxt.action.single_row.replace('{cols}', row)
        rows.append(full_row)
    
    rows = "\n".join(rows)
    view.cxt.context.text = view.cxt.context.text.replace('{rows}', rows)
    view.cxt.context.set_storage(
        table_header = table_header,
    )

@view.view_preparation('input')
def input_view_preparation(view: GameView):  
    if not view.cxt.context.memory.step:
        view.cxt.context.memory.step = 0
    
    question = view.cxt.action.questions[view.cxt.context.memory.step]
    view.cxt.context.set_storage(
        question = question.text,
        name   = view.cxt.context.memory.get('name', '-'),
        author = view.cxt.context.memory.get('author', '-'),
        year   = view.cxt.context.memory.get('year', '-'),
        error  = view.cxt.context.memory.get('error', '')
    )


if __name__ == "__main__":
    try:
        view.run_loop(locale.main)
    except Exception as e:
        logger.exception(e)
        input()
