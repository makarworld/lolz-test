from loguru import logger

from src.models import Game
from src.context import Localization
from src.utils import set_console_size
from src.exceptions import *
from src.mcv import ContextStorage, GameModel, GameController, GameView

# set standart console size
set_console_size(70, 41)

# load locale for select language
locale = Localization('all')

# load context
cxt = ContextStorage(locale)

# load MVC (Model, View, Controller)
game_model = GameModel(cxt)
game_controller = GameController(cxt, game_model)
game_view = GameView(cxt, game_model, game_controller)




# # # # # # # # # # # # # # # # # # # # #
#                                       #
#                                       #
#              NAVIGATORS               #
#                                       #
#                                       #
# # # # # # # # # # # # # # # # # # # # # 
# All navigators between system states  #
# # # # # # # # # # # # # # # # # # # # # 

@game_controller.navigator(page_from = 'select_language', buttons = [])
def add_game(ctrl: GameController):
    lang = ctrl.cxt.context.memory.langs[ctrl.model.current_button - 1]
    ctrl.cxt.locale = lang
    ctrl.set_action(ctrl.cxt.locale.main)

@game_controller.navigator(page_from = 'main', buttons = [1])
def add_game(ctrl: GameController):
    ctrl.set_action(ctrl.cxt.locale.add_game)

@game_controller.navigator(page_from = 'main', buttons = [2])
def find_game(ctrl: GameController):
    ctrl.set_action(ctrl.cxt.locale.find_game)

@game_controller.navigator(page_from = 'main', buttons = [3])
def game_list(ctrl: GameController):
    games = list(Game.select())
    if games:
        ctrl.cxt.context.memory.games = list(Game.select())
        ctrl.set_action(ctrl.cxt.locale.game_list)
    else:
        ctrl.cxt.context.storage.status = ctrl.cxt.action.no_games


@game_controller.navigator(page_from = 'game_list', buttons = []) # any button
def game_list_buttons(ctrl: GameController):
    game_index = (ctrl.cxt.action.rows * (ctrl.model.current_page - 1)) + ctrl.model.current_button - 1
    game: Game = ctrl.cxt.context.memory.games[game_index]
    ctrl.cxt.context.memory.current_game = game
    ctrl.cxt.context.set_storage(name = game.name, author = game.author, year = game.year)

    ctrl.set_action(ctrl.cxt.locale.game_page)

@game_controller.navigator(page_from = 'game_page', buttons = [1])
def game_page_edit(ctrl: GameController):
    ctrl.set_action(ctrl.cxt.locale.edit_game)
    game: Game = ctrl.cxt.context.memory.current_game
    ctrl.cxt.context.memory.update(name = game.name, author = game.author, year = game.year)

@game_controller.navigator(page_from = 'game_page', buttons = [2])
def game_page_delete(ctrl: GameController):
    ctrl.cxt.context.storage.status = ctrl.cxt.action.delete # delete
    game: Game = ctrl.cxt.context.memory.current_game
    game.delete_instance()
    ctrl.set_action(ctrl.cxt.locale.main) # to menu

@game_controller.navigator(page_from = 'game_page', buttons = [3])
def game_page_menu(ctrl: GameController):
    ctrl.set_action(ctrl.cxt.locale.game_list) # back




# # # # # # # # # # # # # # # # # # # # #
#                                       #
#                                       #
#           INPUT VALIDATORS            #
#                                       #
#                                       #
# # # # # # # # # # # # # # # # # # # # # 
#      validators for input data        #
# # # # # # # # # # # # # # # # # # # # # 



@game_controller.input_validator(on_page = "add_game")
def add_game_validator(ctrl: GameController):
    # Сохранить игру в бд
    game = Game(
        name = ctrl.cxt.context.memory.name, 
        author = ctrl.cxt.context.memory.author, 
        year = ctrl.cxt.context.memory.year)
    game.save()

    ctrl.cxt.context.storage.status = ctrl.cxt.action.success
    ctrl.set_action(ctrl.cxt.locale.main)

@game_controller.input_validator(on_page = "find_game")
def find_game_validator(ctrl: GameController):
    # если игры не найдены в статус поставить что нет таких и вернуть в меню
    # если найдены отправить на страницы с играми
    query = Game.select()

    if ctrl.cxt.context.memory.name:
        query = query.where(Game.name == ctrl.cxt.context.memory.name)
    if ctrl.cxt.context.memory.author:
        query = query.where(Game.author == ctrl.cxt.context.memory.author)
    if ctrl.cxt.context.memory.year:
        query = query.where(Game.year == ctrl.cxt.context.memory.year)
    
    result = list(query)
    if not result:
        ctrl.cxt.context.storage.status = ctrl.cxt.action.error
        ctrl.set_action(ctrl.cxt.locale.main)
        return
    else:
        ctrl.cxt.context.memory.games = result
        ctrl.set_action(ctrl.cxt.locale.game_list)

@game_controller.input_validator(on_page = "edit_game")
def edit_game_validator(ctrl: GameController):
    # изменение игры
    game: Game = ctrl.cxt.context.memory.current_game
    game.name = ctrl.cxt.context.memory.name if ctrl.cxt.context.memory.name else game.name
    game.author = ctrl.cxt.context.memory.author if ctrl.cxt.context.memory.author else game.author
    game.year = ctrl.cxt.context.memory.year if ctrl.cxt.context.memory.year else game.year
    game.save()

    ctrl.cxt.context.storage.status = ctrl.cxt.action.success
    ctrl.set_action(ctrl.cxt.locale.main)



# # # # # # # # # # # # # # # # # # # # #
#                                       #
#                                       #
#          VIEW PREPARATIONS            #
#                                       #
#                                       #
# # # # # # # # # # # # # # # # # # # # # 
#        prepare text for view          #
# # # # # # # # # # # # # # # # # # # # # 

        
@game_view.view_preparation('selectable')
def selectable_view_preparation(view: GameView):
    if view.cxt.action.name == 'select_language':
        langs = Localization.get_languages()
        view.model.max_button = len(langs)
        view.cxt.context.memory.langs = langs

        rows = []

        for i, lang in enumerate(langs):
            rows.append(
                view.cxt.locale.select_language.lang_row
                .replace('{i}', str(i + 1),)
                .replace('{language}', lang.lang_name if lang.lang_name else lang.language)
                # lang_name from file, is not specified, just language as EN, RU, etc.
            )
        rows = "\n".join(rows)
        view.cxt.context.text = view.cxt.context.text.replace('{rows}', rows)

@game_view.view_preparation('horizontal')
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



@game_view.view_preparation('input')
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




# # # # # # # # # # # # # # # # # # # # #
#                                       #
#                                       #
#                START                  #
#                                       #
#                                       #
# # # # # # # # # # # # # # # # # # # # # 
#           start main loop             #
# # # # # # # # # # # # # # # # # # # # # 



if __name__ == "__main__":
    try:
        game_view.run_loop(locale.select_language)
    except Exception as e:
        logger.exception(e)
        input()
