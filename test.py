from src.utils import LocalMemory


test = LocalMemory()

print(test)
print(test.get('key', '-'))
test.key = 1
print(test.get('key', '-'))
test.pop('key')
print(test.get('key', '-'))
print(test.get('key', '-'))
print(test)

