from typing import Callable




class Tests:
    @staticmethod
    def return_error(v: str, err: Exception): 
        return str(err) 

    @staticmethod
    def run_test(func: Callable):
        results: Tests = func()
        print(f"[TEST] {func.__name__} | PASSED: {results.passed} | FAILED: {results.failed}")
        if results.errors:
            print(f"[ERRORS] {func.__name__} | {results.errors}")

    def __init__(self):
        self.errors = []
        self.passed = 0
        self.failed = 0
    
    def _assert(self, value, expected):
        try:
            assert value == expected, value
            self.passed += 1
        except AssertionError as e:
            self.errors.append(e)
            self.failed += 1


# TESTS
def test_inputs():
    from src.inputs import InputManager
    def test_int():
        tests = Tests()
        tests._assert(InputManager.get_input(int, on_error = Tests.return_error, debug_value = '1'), 1)
        tests._assert(InputManager.get_input(int, on_error = Tests.return_error, debug_value = '12'), 12)
        tests._assert(InputManager.get_input(int, on_error = Tests.return_error, debug_value = '-9_9_9_9 '), -9999)
        tests._assert(InputManager.get_input(int, on_error = Tests.return_error, debug_value = '99_99'), 9999)
        tests._assert(InputManager.get_input(int, on_error = Tests.return_error, debug_value = '99 99'), 9999)

        tests._assert(InputManager.get_input(int, on_error = Tests.return_error, debug_value = '1.'), 'Error while validating input "1." as int')
        tests._assert(InputManager.get_input(int, on_error = Tests.return_error, debug_value = '1.2'), 'Error while validating input "1.2" as int')
        tests._assert(InputManager.get_input(int, on_error = Tests.return_error, debug_value = '.99,99'), 'Error while validating input ".99,99" as int')
        tests._assert(InputManager.get_input(int, on_error = Tests.return_error, debug_value = '._9 9,99'), 'Error while validating input "._9 9,99" as int')

        return tests
    
    def test_float():
        tests = Tests()
        tests._assert(InputManager.get_input(float, on_error = Tests.return_error, debug_value = '1.1'), 1.1)
        tests._assert(InputManager.get_input(float, on_error = Tests.return_error, debug_value = '1.099999'), 1.099999)
        tests._assert(InputManager.get_input(float, on_error = Tests.return_error, debug_value = '1.80000000000001'), 1.80000000000001)
        tests._assert(InputManager.get_input(float, on_error = Tests.return_error, debug_value = '.00_00'), 0.0)
        tests._assert(InputManager.get_input(float, on_error = Tests.return_error, debug_value = '-0,05'), -0.05)

        tests._assert(InputManager.get_input(float, on_error = Tests.return_error, debug_value = '1.1.1'), 'Error while validating input "1.1.1" as float')
        tests._assert(InputManager.get_input(float, on_error = Tests.return_error, debug_value = '1.1.'), 'Error while validating input "1.1." as float')
        tests._assert(InputManager.get_input(float, on_error = Tests.return_error, debug_value = '.-0'), 'Error while validating input ".-0" as float')

        return tests

    def test_str():
        tests = Tests()

        tests._assert(InputManager.get_input(str, on_error = Tests.return_error, debug_value = '1'), '1')
        tests._assert(InputManager.get_input(str, on_error = Tests.return_error, debug_value = '1.test.sdsadw'), '1.test.sdsadw')

        tests._assert(InputManager.get_input(str, on_error = Tests.return_error, debug_value = 'https://google.com', regex_pattern = r'https?://.+\..+'), 
            'https://google.com')
        tests._assert(InputManager.get_input(str, on_error = Tests.return_error, debug_value = 'https://google.com', regex_pattern = r'error pattern'), 
            'Error while validating input "https://google.com" as str with regex pattern "error pattern"')
    
        return tests

    def test_bool():
        tests = Tests()

        tests._assert(InputManager.get_input(bool, on_error = Tests.return_error, debug_value = 'true'), True)
        tests._assert(InputManager.get_input(bool, on_error = Tests.return_error, debug_value = 'YES'), True)
        tests._assert(InputManager.get_input(bool, on_error = Tests.return_error, debug_value = 'Y'), True)
        tests._assert(InputManager.get_input(bool, on_error = Tests.return_error, debug_value = 'tru'), True)
        tests._assert(InputManager.get_input(bool, on_error = Tests.return_error, debug_value = '+'), True)

        tests._assert(InputManager.get_input(bool, on_error = Tests.return_error, debug_value = 'false'), False)
        tests._assert(InputManager.get_input(bool, on_error = Tests.return_error, debug_value = 'No'), False)
        tests._assert(InputManager.get_input(bool, on_error = Tests.return_error, debug_value = 'n'), False)
        tests._assert(InputManager.get_input(bool, on_error = Tests.return_error, debug_value = 'fals'), False)
        tests._assert(InputManager.get_input(bool, on_error = Tests.return_error, debug_value = '-'), False)

        return tests

    def test_list():
        tests = Tests()

        tests._assert(InputManager.get_input(list, on_error = Tests.return_error, debug_value = '1,2,3'), ['1', '2', '3'])
        tests._assert(InputManager.get_input(list, on_error = Tests.return_error, debug_value = 'YES'), ['YES'])
        tests._assert(InputManager.get_input(list, on_error = Tests.return_error, debug_value = '1,'), ['1', ''])
        tests._assert(InputManager.get_input(list, on_error = Tests.return_error, debug_value = 'a,b,c,d,e'), ['a', 'b', 'c', 'd', 'e'])

        return tests


    Tests.run_test(test_int)
    Tests.run_test(test_float)
    Tests.run_test(test_str)
    Tests.run_test(test_bool)
    Tests.run_test(test_list)

if __name__ == "__main__":
    test_inputs()