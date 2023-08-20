from abc import ABC
import re
from typing import Any, Callable


from src.exceptions import InputValidationError

class AbstractInputManager(ABC):
    def get_input(cls, _type: str, on_error: Callable, 
                  on_success: Callable = None, custom_validation: Callable = None, 
                  regex_pattern: str = None, debug_value: str = None) -> Any: ...
    def validate(cls, text: str, _type: str, *args, **kwargs) -> Any: ...
    def bool_validation(value: str) -> bool: ...
    def str_validation(value: str, regex_pattern: str  = None) -> str: ...
    def int_validation(value: str) -> int: ...
    def float_validation(value: str) -> float: ...
    def list_validation(value: str) -> list: ...

class InputManager(AbstractInputManager):
    """Input manager with basic validation"""
    @classmethod
    def get_input(cls, 
                  _type: object, 
                  on_error: Callable, 
                  on_success: Callable = None, 
                  custom_validation: Callable = None,
                  regex_pattern: str = None,
                  debug_value: str = None) -> Any: 
        """
        Input text from user, validate and return it as required type
        If input is invalid, call on_error
        If input is valid, and on_success is specified, call on_success
        else return validated value
        """
        try:
            # if debug -> skip input
            value = input() if not debug_value else debug_value
            # if not custom_validation -> run default
            if not custom_validation:
                # strings validation may consist regex pattern
                if _type == str and regex_pattern:
                    result = cls.validate(value, _type.__name__, regex_pattern = regex_pattern)
                else:
                    result = cls.validate(value, _type.__name__)

            else:
                # run custom validation
                result = custom_validation(value)

            if on_success:
                # run on_success if provided
                return on_success(result)
            
            # return result - value with type = _type
            return result
        
        except Exception as e:
            # run on_error handler
            return on_error(value, e)

    @classmethod
    def validate(cls, text: str, _type: str, *args, **kwargs) -> Any: 
        """
        Validate text and return it as required type
        """
        validator = object.__getattribute__(cls, f"{_type}_validation")
        return validator(value = text, *args, **kwargs)

    @staticmethod
    def bool_validation(value: str) -> bool: 
        """
        Validate value as bool
        """
        if value.lower() in (
                    'true', 'tru', 'yes', 
                    'da', '1', '+', 'y'):
            return True
        
        elif value.lower() in (
                    'false', 'fals', 'no', 
                    'net', '0', '-', 'n'):
            return False
        
        else:
            raise InputValidationError(f"Error while validating input \"{value}\" as bool")
    
    @staticmethod
    def str_validation(value: str, regex_pattern: str = None) -> str:
        if regex_pattern:
            match = re.match(regex_pattern, value)
            if not match:
                raise InputValidationError(f"Error while validating input \"{value}\" as str with regex pattern \"{regex_pattern}\"")
            return value
        return value
    
    @staticmethod
    def int_validation(value: str) -> int:
        svalue = value.replace('_', '').replace(' ', '')
        try:
            return int(svalue)
        except ValueError:
            raise InputValidationError(f"Error while validating input \"{value}\" as int")

    @staticmethod
    def float_validation(value: str) -> float:
        svalue = value.replace(',', '.').replace('_', '').replace(' ', '')
        try:
            return float(svalue)
        except ValueError:
            raise InputValidationError(f"Error while validating input \"{value}\" as float")
    
    @staticmethod
    def list_validation(value: str) -> list:
        """validate list as one,two,three"""
        return value.split(',')
