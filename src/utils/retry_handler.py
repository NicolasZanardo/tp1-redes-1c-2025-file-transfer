import socket
from .logger import Logger

class RetryHandler:
    def __init__(self, retries=5):
        self.retries = retries

    def run(self, 
            action: callable, 
            on_timeout: callable = None,
            logger_who = None,
            action_description = "Retrying action",
            ):
        for attempt in range(1, self.retries + 1):
            try:
                return action(attempt)
            except socket.timeout:
                msg = f"Timeout on attempt {attempt}: {action_description}"
                Logger.debug(
                    who=logger_who, 
                    message=msg
                )

                if on_timeout:
                    on_timeout(attempt)
        
        Logger.error(
            who=logger_who, 
            message=f"Failed after {self.retries} retries: {action_description}"
        )
        return False