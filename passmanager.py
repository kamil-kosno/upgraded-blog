from werkzeug import security as sec

SALT_LENGTH = 8
ENCRYPTION = 'pbkdf2:sha256'


class PasswordManager:
    @staticmethod
    def get_hash(password):
        return sec.generate_password_hash(password=password, method=ENCRYPTION, salt_length=SALT_LENGTH)


