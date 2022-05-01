import shelve


class ShelveWrapper:

    def __init__(self, db_name):
        self.db_name = db_name

    def insert_batch(self, **kwargs):
        with shelve.open(self.db_name) as db:
            for (k, v) in kwargs:
                db[k] = v

    def insert(self, k: str, v):
        with shelve.open(self.db_name) as db:
            db[k] = v

    def read(self, k: str):
        with shelve.open(self.db_name) as db:
            return db[k]

    def read_all(self):
        with  shelve.open(self.db_name) as db:
            return db.items()

    def del_key(self, k: str):
        with shelve.open(self.db_name) as db:
            del db[k]
