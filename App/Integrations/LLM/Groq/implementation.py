from .concrete import PyGroq

class PyGroqImplementation(PyGroq):
    _instance = None 

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PyGroq, cls).__new__(cls) 
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            super().__init__()
            self._initialized = True