from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher


# Инициализировать контекст хэширования паролей
pwd_context = PasswordHash((BcryptHasher(),))


def hash_password(password: str) -> str:
    """
    Генерирует криптографический хэш для переданного открытого пароля.

    :param password: Исходный открытый пароль.
    :return: Безопасный хэш пароля с солью в формате bcrypt.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Сравнивает открытый пароль с ранее сохраненным хэшем.

    :param plain_password: Пароль, введенный пользователем.
    :param hashed_password: Хэш пароля, извлеченный из базы данных.
    :return: True, если пароль верен, иначе False.
    """
    return pwd_context.verify(plain_password, hashed_password)