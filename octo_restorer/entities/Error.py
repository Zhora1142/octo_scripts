from colorama import Fore


class Error:
    error_type = ''
    message = ''
    exception = None

    def __init__(self, error_type, message, exception=None):
        self.error_type = error_type
        self.message = message
        self.exception = exception

    def __str__(self):
        return f'{Fore.RED}({self.error_type}) {self.message}{f": {type(self.exception)}" if self.exception else ""}{Fore.RESET}'
