# Ленивые импорты
import numpy as np

class BatchGenerator:
    def __init__(self, batch_size=10000):
        self.batch_size = batch_size
        self._pl = None
        self._fake = None
    
    @property
    def pl(self):
        if self._pl is None:
            import polars as pl
            self._pl = pl
        return self._pl
    
    @property
    def fake(self):
        if self._fake is None:
            from faker import Faker
            self._fake = Faker()
        return self._fake
