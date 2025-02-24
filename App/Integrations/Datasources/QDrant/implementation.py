from .concrete import QDrantConcrete

class QDrantImplementation(QDrantConcrete):
    _instance = None 

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(QDrantConcrete, cls).__new__(cls) 
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            super().__init__()
            self._initialized = True