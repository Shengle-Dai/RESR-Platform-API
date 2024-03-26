from app import db

class User(db.Model):
    """
    User Model
    """

    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key = True, autoincrement = True)
    username = db.Column(db.String, nullable = False)
    password = db.Column(db.String, nullable = False)

    def __init__(self, **kwargs):
        """
        Initialize a user object
        """

        self.username = kwargs.get("username", "")
        self.password = kwargs.get("password", "")

    def serialize(self):
        """
        Serialize a user object
        """
        return {
            "id": self.id,
            "username": self.username
        }