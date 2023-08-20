from typing import Any, List, Callable

from src.inputs import InputManager
from src.context import Localization, Context
from src.utils import (
    set_console_size, wait_key, nth_repl, 
    KeyMap, ControlKey, LocalMemory, 
    ViewPreparation, InputHandler, Navigator
)
from src.exceptions import *

class ContextStorage:
    """Storage for Context, Model"""
    def __new__(cls, *args, **kwargs):
        it = cls.__dict__.get('__it__')
        if it is not None:
            return it 
        cls.__it__ = it = object.__new__(cls)
        it.init(*args, **kwargs)
        return it
    
    def init(self, locale: Localization) -> None:
        self.context = Context()
        self.action = None
        self.locale = locale

class GameModel:
    """Store pagination context, Model"""
    def __init__(self, cxt: ContextStorage) -> None:
        self.cxt = cxt

        # Значение текущей выбранной кнопки
        self.current_button = 1
        self.max_button = None

        # Значение текущей страницы
        self.current_page = 1
        self.max_page = None

    def set_button(self, button: int):
        """Установить текущую кнопку"""
        self.current_button = max(1, min(self.max_button, button))

    def set_page(self, page: int):
        """Установить текущую страницу"""
        last = self.current_page
        self.current_page = max(1, min(self.max_page, page))
        if last != self.current_page:
            self.current_button = 1

    def clear_temp(self):
        """Очистить атрибуты name, author, year из памяти"""
        try: self.cxt.context.memory.pop('name') 
        except: pass
        try: self.cxt.context.memory.pop('author') 
        except: pass
        try: self.cxt.context.memory.pop('year') 
        except: pass

class GameController:
    """Make operations with user, edit context, Controller"""
    def __init__(self, cxt: ContextStorage, model: GameModel):
        self.cxt = cxt
        self.model = model
        self.last_key = ''
        self.navigators: List[Navigator] = []
        self.inputs_validators: List[InputHandler] = []

    # INPUT HANDLERS
    def register_inputs_validator(self, callback: Callable, on_page: str):
        """
        Зарегистрировать inputs_validator с заданной страницы
        Метод будет вызван когда все инпуты будут заполнены
        Инпуты сохраняются в памяти контекста
        """ 
        self.inputs_validators.append(
            InputHandler(
                callback = callback,
                on_page = on_page
            )
        )

    def call_inputs_validator(self): 
        """Найти и вызвать инпут-валидатор, если не задан вызвать ошибку"""
        for handler in self.inputs_validators:
            if (handler.on_page == self.cxt.action.name):
                return handler.callback(self)
            
        raise InputValidatorNotExist(f"Validator {self.cxt.action.name} not found")
    
    
    def input_validator(self, on_page: str): 
        """Декоратор для создания валидатора как функции"""
        def decorator(callback):
            self.register_inputs_validator(callback, on_page)

            return callback
        return decorator

    # NAVIGATORS
    def register_navigator(self, callback, page: str, buttons: List[int]):
        """
        Зарегистрировать навигатор после нажатия заданной кнопки на заданной странице
        Метод должен перенаправить на следующую страницу
        """ 
        self.navigators.append(
            Navigator(
                callback = callback,
                page = page,
                buttons = buttons
            )
        )
    
    def call_navigator(self) -> None:
        """Найти и вызвать навигатор, если не задан вызвать ошибку"""
        for nav in self.navigators:
            if (nav.page == self.cxt.action.name) and\
               ((self.model.current_button in nav.buttons) or (not nav.buttons)):
                return nav.callback(self)
            
        raise PageNotExist(f"Page {self.cxt.action.name} with button {self.model.current_button} not found")
    
    def navigator(self, page_from: str, buttons: List[int]):
        """Декоратор для создания навигатора как функции"""
        def decorator(callback):
            self.register_navigator(callback, page_from, buttons)

            return callback
        return decorator

    def press_key(self, key: str):
        """
        Ивент нажатия на клавишу, вызвает действие если оно нужно
        """
        arrow = (self.last_key + key).encode()
        self.last_key = key

        if self.cxt.action.selectable:
            if KeyMap.whatkey(key, arrow) == ControlKey.UP:
                self.model.set_button(self.model.current_button - 1)

            elif KeyMap.whatkey(key, arrow) == ControlKey.DOWN:
                self.model.set_button(self.model.current_button + 1)

        if self.cxt.action.horizontal: 
            if KeyMap.whatkey(key, arrow) == ControlKey.LEFT:
                self.model.set_page(self.model.current_page - 1)

            elif KeyMap.whatkey(key, arrow) == ControlKey.RIGHT:
                self.model.set_page(self.model.current_page + 1)

        if KeyMap.whatkey(key) == ControlKey.ESC:
            self.set_action(self.cxt.locale.main)

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
        """Ивент ввода значения, валидация и выход в меню если требуется"""
        if isinstance(value, tuple):
            if (value[0] != '' and question.nullable is False) and value[0] != '-':
                self.cxt.context.memory.error = question.error
                return
            
            elif value[0].strip() == '-':
                self.set_action(self.cxt.locale.main)
                return

            else:
                value = value[0]

        elif value == '-':
            self.set_action(self.cxt.locale.main)
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
        """
        Запрос к контроллеру на выполнение нужного действия на странице
        Ожидания ввода или нажатия клавиши
        """
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
        # Сменить состояние всей системы
        # поменять текущую страницу
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
    """Print page with current context, View"""
    def __init__(self, cxt: ContextStorage, model: GameModel, controller: GameController):
        self.cxt = cxt
        self.model = model
        self.controller = controller
        self.preparation_handlers: List[ViewPreparation] = []

    def register_preparation(self, callback: Callable, key: str): 
        """Зарегистрировать предварительный обработчик данных из конфига страницы"""
        self.preparation_handlers.append(
            ViewPreparation(
                callback = callback,
                key = key
            )
        )
    def call_preparation(self, key: str): 
        """Вызвать предварительный обработчик данных если он существует для данного ключа"""
        for preparation in self.preparation_handlers:
            if (preparation.key == key):
                return preparation.callback(self)
    
    def view_preparation(self, key: str): 
        """Декоратор для создания предварительного обработчика как функции"""
        def decorator(callback):
            self.register_preparation(callback, key)

            return callback
        return decorator


    def show(self):
        """Главная функция отрисовки страницы"""
        for key, value in self.cxt.action.items():
            if value:
                # вызов предварительного обработчика если есть значение
                self.call_preparation(key)

        if self.cxt.action.selectable: 
            # отобразить текущую выбранную кнопку если страница поддерживает кнопки
            # replace selected button
            self.cxt.context.text = nth_repl(self.cxt.context.text, '{select}', '[>]', self.model.current_button)
            # replace other buttons
            self.cxt.context.text = self.cxt.context.text.replace('{select}', '   ',)
        
        if '{status}' in self.cxt.context.text:
            # Замена статуса, если не указан то поставить пустой, если указан то поставить '* ' перед ним
            if not self.cxt.context.storage.get('status'):
                # set status after first start for avoid error
                self.cxt.context.storage['status'] = ''
            elif not self.cxt.context.storage['status'].startswith('* '):
                self.cxt.context.storage['status'] = '* ' + self.cxt.context.storage['status']
        
        # взять баннер для текущей локализации и удалить с него "
        banner = self.cxt.locale.banner
        if banner.strip().startswith('"') and\
           banner.strip().endswith('"'):
            banner = banner.strip()[1:-1]

        # посчитать количество строк для отображения, подогнать под них размер консоли
        rows = (banner + self.cxt.context.text).split('\n')
        # если на странице есть инпут, то добавить 1 строку
        len_rows = len(rows) + (1 if self.cxt.action.input else 0)
        if self.cxt.context.memory.last_size != len_rows:
            self.cxt.context.memory.last_size = len_rows
            set_console_size(70, len_rows)

        # отобразить баннер и страницу
        print(banner)
        self.cxt.context.show(endless = self.cxt.action.input) # if input is true = endless mode

        # set previous text for clear all edits
        self.cxt.context.text = self.cxt.action.text 
    
    def clear(self):
        # очистить консоль
        self.cxt.context.clear_console()

    def run_loop(self, first_page: Localization):
        # запустить главный луп программы
        self.controller.set_action(first_page)

        while True:
            self.show()
            self.controller.request()
            self.clear()