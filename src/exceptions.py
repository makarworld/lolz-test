
class GameException(Exception):
    pass

class InputValidationError(GameException):
    pass

class InvalidLanguageError(GameException):
    pass

class PageNotExist(GameException): 
    pass

class InputValidatorNotExist(GameException): 
    pass