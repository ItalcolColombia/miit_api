import re

def password_complexity_validator(value: str) -> str:
    """
    Password complexity validator
    Requires:
        - number
        - uppercase letter
        - special character
    """
    if not re.findall(r"\d", value):
        raise ValueError("La contraseña debe contener al menos contener un número.")

    if not re.findall(r"[A-Z]", value):
        raise ValueError("La contraseña debe contener al menos una mayúscula.")

    if not re.findall(r'[!¡/@#$%^&*(),.¿?":{}|<>]', value):
        raise ValueError("La contraseña debe contener al menos un carácter especial.")

    return value