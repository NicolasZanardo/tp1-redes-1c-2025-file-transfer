from abc import ABC, abstractmethod

class SWState(ABC):
    def __init__(self, ctx):
        self.ctx = ctx

    @abstractmethod
    def on_enter(self):
        pass
