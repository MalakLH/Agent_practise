"""here are some tests for the calculator"""

from calculator import add, subtract, multiply, divide

def test_add():
    assert add(-1, 1) == 0

def test_subtract():
    assert subtract(0, 5) == -5

def test_multiply():
    assert multiply(2, 3) == 6

def test_divide():
    assert divide(6, 3) == 2