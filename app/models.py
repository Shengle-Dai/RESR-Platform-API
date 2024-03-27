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
    
class MaterialMainCategory(db.Model):
    """
    Material Main Category Model
    """

    __tablename__ = "material_main_category"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True, nullable=False)

    # Relationship: A main category has many subcategories
    subcategories = db.relationship('MaterialSubCategory', backref='material_main_category', lazy=True)

    def __init__(self, **kwargs):
        """
        Initialize a material main category object
        """
        self.name = kwargs.get("name", "")

    def serialize(self):
        """
        Serialize a material main category object
        """
        return {
            "id": self.id,
            "name": self.name
        }


class MaterialSubCategory(db.Model):
    """
    Material Sub Category Model
    """

    __tablename__ = "material_sub_category"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True, nullable=False)
    material_main_category_id = db.Column(db.Integer, db.ForeignKey('material_main_category.id'), nullable=False)

    # Relationship: A subcategory has many materials
    materials = db.relationship('Material', backref='material_sub_category', lazy=True)

    def __init__(self, **kwargs):
        """
        Initialize a material sub category object
        """
        self.name = kwargs.get("name", "")
        self.material_main_category_id = kwargs.get("material_main_category_id")

    def serialize(self):
        """
        Serialize a material sub category object
        """
        return {
            "id": self.id,
            "name": self.name,
            "material_main_category_id": self.material_main_category_id
        }


class Material(db.Model):
    """
    Material Model
    """

    __tablename__ = "material"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True, nullable=False)
    material_sub_category_id = db.Column(db.Integer, db.ForeignKey('material_sub_category.id'), nullable=False)

    def __init__(self, **kwargs):
        """
        Initialize a material object
        """
        self.name = kwargs.get("name", "")
        self.material_sub_category_id = kwargs.get("material_sub_category_id")

    def serialize(self):
        """
        Serialize a material object
        """
        return {
            "id": self.id,
            "name": self.name,
            "material_sub_category_id": self.material_sub_category_id
        }
