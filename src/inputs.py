from abc import ABC
import re
from typing import Any, Callable

from src.exceptions import InputValidationError

class AbstractInputManager(ABC):
    def get_input(cls, _type: str) -> Any: ...
    def validate(cls, text: str, _type: str) -> Any: ...
    def bool_validation(value: str) -> bool: ...
    def str_validation(value: str, pattern: str  = None) -> str: ...
    def int_validation(value: str) -> int: ...
    def float_validation(value: str) -> float: ...
    def list_validation(value: str) -> list: ...

class InputManager(AbstractInputManager):
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
            value = input() if not debug_value else debug_value

            if not custom_validation:
                if _type == str and regex_pattern:
                    result = cls.validate(value, _type.__name__, regex_pattern = regex_pattern)
                else:
                    result = cls.validate(value, _type.__name__)

            else:
                result = custom_validation(value)

            if on_success:
                return on_success(result)
            
            return result
        
        except Exception as e:
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
