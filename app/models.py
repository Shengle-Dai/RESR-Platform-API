from app import db


class User(db.Model):
    """
    User Model
    """

    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)

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
        return {"id": self.id, "username": self.username}


class CoatingCategory(db.Model):
    """
    Coating Category Model
    """

    __tablename__ = "coating_category"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True, nullable=False)
    coatings = db.relationship("Coating", backref="coating_category", lazy=True)
    images = db.relationship("Image", backref="coating_category", lazy=True)

    def __init__(self, **kwargs):
        """
        Initialize a coating category object
        """
        self.name = kwargs.get("name", "")

    def serialize(self):
        """
        Serialize a coating category object
        """
        return {
            "id": self.id,
            "name": self.name,
            "coatings": [coating.serialize() for coating in self.coatings],
            "images": [image.serialize() for image in self.images],
        }

    def simple_serialize(self):
        """
        Serialize a coating category object
        """
        return {"id": self.id, "name": self.name}


class Coating(db.Model):
    """
    Coating Model
    """

    __tablename__ = "coating"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sub_category = db.Column(db.String, nullable=False)
    thickness = db.Column(db.String, nullable=False)
    color = db.Column(db.String, nullable=False)
    category_id = db.Column(
        db.Integer, db.ForeignKey("coating_category.id"), nullable=False
    )

    def __init__(self, **kwargs):
        """
        Initialize a coating object
        """
        self.sub_category = kwargs.get("sub_category", "")
        self.thickness = kwargs.get("thickness", "")
        self.color = kwargs.get("color", "")
        self.category_id = kwargs.get("category_id", -1)

    def serialize(self):
        """
        Serialize a coating object
        """
        return {
            "id": self.id,
            "main_category": CoatingCategory.query.get(self.category_id).name,
            "sub_category": self.sub_category,
            "thickness": self.thickness,
            "color": self.color,
        }


class Shape(db.Model):
    """
    Shape Model
    """

    __tablename__ = "shape"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True, nullable=False)
    images = db.relationship("Image", backref="shape", lazy=True)

    def __init__(self, **kwargs):
        """
        Initialize a shape object
        """
        self.name = kwargs.get("name", "")

    def serialize(self):
        """
        Serialize a shape object
        """
        return {
            "id": self.id,
            "name": self.name,
            "images": [image.serialize() for image in self.images],
        }

    def simple_serialize(self):
        """
        Serialize a shape object
        """
        return {"id": self.id, "name": self.name}


class Image(db.Model):
    """
    Image Model
    """

    __tablename__ = "image"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    base64_data = db.Column(db.String, nullable=False)
    shape_id = db.Column(db.Integer, db.ForeignKey("shape.id"), nullable=False)
    category_id = db.Column(
        db.Integer, db.ForeignKey("coating_category.id"), nullable=False
    )

    def __init__(self, **kwargs):
        """
        Initialize an image object
        """
        self.base64_data = kwargs.get("base64_data", "")
        self.name = kwargs.get("name", "")
        self.shape_id = kwargs.get("shape_id", -1)
        self.category_id = kwargs.get("category_id", -1)

    def serialize(self):
        """
        Serialize an image object
        """
        return {"id": self.id, "base64_data": self.base64_data}


class MaterialCategory(db.Model):
    """
    Material Category Model
    """

    __tablename__ = "material_category"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True, nullable=False)
    is_rare_earth = db.Column(db.Boolean, nullable=False)
    materials = db.relationship("Material", backref="material_category", lazy=True)

    def __init__(self, **kwargs):
        """
        Initialize a material category object
        """
        self.name = kwargs.get("name", "")
        self.is_rare_earth = kwargs.get("is_rare_earth", False)

    def serialize(self):
        """
        Serialize a material category object
        """
        return {
            "id": self.id,
            "name": self.name,
            "is_rare_earth": self.is_rare_earth,
            "materials": [material.serialize() for material in self.materials],
        }

    def simple_serialize(self):
        """
        Serialize a material category object
        """
        return {"id": self.id, "name": self.name, "is_rare_earth": self.is_rare_earth}


class Material(db.Model):
    """
    Material Model
    """

    __tablename__ = "material"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    grade = db.Column(db.String, nullable=False)
    br_t = db.Column(db.Integer, nullable=False)
    hcb_kA_m = db.Column(db.Integer, nullable=False)
    bh_max_kj_m3 = db.Column(db.Integer, nullable=False)
    category_id = db.Column(
        db.Integer, db.ForeignKey("material_category.id"), nullable=False
    )

    def __init__(self, **kwargs):
        """
        Initialize a material object
        """
        self.grade = kwargs.get("grade", "")
        self.br_t = kwargs.get("br_t", -1)
        self.hcb_kA_m = kwargs.get("hcb_kA_m", -1)
        self.bh_max_kj_m3 = kwargs.get("bh_max_kj_m3", -1)
        self.category_id = kwargs.get("category_id", -1)

    def serialize(self):
        """
        Serialize a material object
        """
        return {
            "id": self.id,
            "grade": self.grade,
            "br_t": self.br_t,
            "hcb_kA_m": self.hcb_kA_m,
            "bh_max_kj_m3": self.bh_max_kj_m3,
        }

    def simple_serialize(self):
        """
        Serialize a material object
        """
        return {"id": self.id, "grade": self.grade}
