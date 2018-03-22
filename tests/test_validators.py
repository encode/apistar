from apistar import validators
from apistar.exceptions import ValidationError
import pytest 

def test_email():
    a = validators.Email()
    assert a.validate('coucou@hello.fr') == "coucou@hello.fr"
    a = validators.Email()
    with pytest.raises(ValidationError):
        a.validate("hello")
