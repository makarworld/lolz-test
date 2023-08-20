
class GameException(Exception):
    pass

class InputError(GameException):
    pass

class InputValidationError(GameException):
    pass

class ContextError(GameException):
    pass

class InvalidLanguageError(GameException):
    pass

class ReadYamlError(GameException):
    pass

class UnknownError(GameException):
    pass

class PageNotExist(GameException): 
    pass

class InputValidatorNotExist(GameException): 
    pass