import MySQLdb as mdb

class MysqlStorage:

    def __init__(self,
                 host_db,
                 user_db,
                 password_db,
                 name_db):

        self.host_db = host_db
        self.user_db = user_db
        self.password_db = password_db
        self.name_db = name_db

        self.connect_db()

    def connect_db(self):

        self.db = mdb.connect(
            host=self.host_db,
            user=self.user_db,
            passwd=self.password_db,
            db=self.name_db,
            charset='utf-8',
            use_unicode=True)

    def get_cursor(self, query, params=None):

        try:
            cursor = self.db.cursor()
            cursor.execute(query) if params is None else cursor.execute(query, params)
        except Exception as e:
            self.connect_db()
            cursor = self.db.cursor()
            cursor.execute(query) if params is None else cursor.execute(query, params)

        self.db.commit()
        return cursor

