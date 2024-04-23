from flask import request, jsonify, Blueprint, current_app
import pandas as pd
from werkzeug.utils import secure_filename
from app import db
from app.models import (
    User,
    Coating,
    CoatingCategory,
    Shape,
    Image,
    MaterialCategory,
    Material,
)
import base64, shutil, tempfile, io, os, zipfile


#### GENERALIZE RETURN ####


def success_response(body, code=200):
    """
    Generates a success response.
    :param body: The response body.
    :param code: HTTP status code, default is 200.
    :return: JSON response and HTTP status code.
    """
    return jsonify(body), code


def failure_response(message, code=404):
    """
    Generates a failure response.
    :param message: Error message.
    :param code: HTTP status code, default is 404.
    :return: JSON response and HTTP status code.
    """
    return jsonify({"error": message}), code


#### HELPER METHODS ####


def process_excel_file(filepath):
    # Load the Excel file
    df = pd.read_excel(filepath, engine="openpyxl")

    # Standardize column headers: lower case and replace spaces with underscores
    df.columns = df.columns.str.lower().str.replace(" ", "")

    return df


def allowed_file_excel(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in {"xlsx", "xls"}


### BLUEPRINTS ###

user_blueprint = Blueprint("user_blueprint", __name__)
coating_blueprint = Blueprint("coating_blueprint", __name__)
shape_blueprint = Blueprint("shape_blueprint", __name__)
material_blueprint = Blueprint("material_blueprint", __name__)


### USER ROUTES ###


@user_blueprint.route("/", methods=["POST"])
def create_user():
    """
    Create a new user
    """
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return failure_response("Missing username or password", 400)

    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()

    return success_response(new_user.serialize(), 201)


@user_blueprint.route("/", methods=["GET"])
def get_users():
    """
    Get all users
    """
    users = User.query.all()
    return success_response([user.serialize() for user in users])


### COATING ROUTES ###


@coating_blueprint.route("/categories", methods=["GET"])
def get_all_coating_categories():
    """
    Get all coating categories
    """
    categories = CoatingCategory.query.all()
    return success_response([category.simple_serialize() for category in categories])


@coating_blueprint.route("/categories", methods=["POST"])
def create_coating_category():
    """
    Create a new coating category
    """
    data = request.json
    name = data.get("name")

    if not name:
        return failure_response("Missing name", 400)

    new_category = CoatingCategory(name=name)
    db.session.add(new_category)
    db.session.commit()

    return success_response(new_category.serialize(), 201)


@coating_blueprint.route("/categories/<int:category_id>", methods=["GET"])
def get_coating_category(category_id):
    """
    Get a coating category by ID
    """
    category = CoatingCategory.query.get(category_id)
    if category:
        return success_response(category.serialize())
    return failure_response("Category not found", 404)


@coating_blueprint.route("/", methods=["GET"])
def get_all_coatings():
    """
    Get all coatings
    """
    coatings = Coating.query.all()
    return success_response([coating.serialize() for coating in coatings])


@coating_blueprint.route("/<int:coating_id>", methods=["GET"])
def get_coating(coating_id):
    """
    Get a coating by ID
    """
    coating = Coating.query.get(coating_id)
    if coating:
        return success_response(coating.serialize())
    return failure_response("Coating not found", 404)


@coating_blueprint.route("/", methods=["POST"])
def create_coating():
    """
    Create a new coating
    """
    data = request.json
    name = data.get("name")
    sub_category = data.get("sub_category")
    thickness = data.get("thickness")
    color = data.get("color")

    if not name or not sub_category or not thickness or not color:
        return failure_response("Missing required fields", 400)

    new_coating = Coating(
        name=name, sub_category=sub_category, thickness=thickness, color=color
    )
    db.session.add(new_coating)
    db.session.commit()

    return success_response(new_coating.serialize(), 201)


@coating_blueprint.route("/upload_excel", methods=["POST"])
def upload_coatings():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    file_extension = os.path.splitext(file.filename)[1]

    if file_extension.lower() == ".xls":
        df = pd.read_excel(file, engine="xlrd")
    elif file_extension.lower() == ".xlsx":
        df = pd.read_excel(file, engine="openpyxl")
    else:
        return jsonify({"error": "Invalid file format"}), 400

    df.columns = df.columns.str.lower().str.replace(" ", "")

    for index, row in df.iterrows():
        # Check and create CoatingCategory if needed
        category_name = row["category"]
        category = CoatingCategory.query.filter_by(name=category_name).first()
        if not category:
            category = CoatingCategory(name=category_name)
            db.session.add(category)
            db.session.flush()  # To get the category_id before committing

        # Create a new Coating
        new_coating = Coating(
            sub_category=row["subcategory"],
            thickness=row["thickness"],
            color=row["color"],
            category_id=category.id,
        )
        db.session.add(new_coating)

    db.session.commit()
    return jsonify({"message": "Coatings uploaded successfully"}), 201


@coating_blueprint.route("/categories/upload_zip", methods=["POST"])
def upload_coating_categories_from_zip():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    zip_file = request.files["file"]
    if not zip_file.filename.endswith(".zip"):
        return jsonify({"error": "The file must be a zip"}), 400

    # Unzip the file into a temporary directory
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(io.BytesIO(zip_file.read())) as z:
        z.extractall(temp_dir)

    # Process each directory in the first level directory of the extracted folder
    first_level_directory = next(os.walk(temp_dir))[1][0]
    category_dir = os.path.join(temp_dir, first_level_directory)

    for category_name in os.listdir(category_dir):
        if category_name == "__MACOSX":
            continue
        category_path = os.path.join(category_dir, category_name)
        if os.path.isdir(category_path):
            # Create a new coating category or get existing one
            category = CoatingCategory.query.filter_by(name=category_name).first()
            if not category:
                category = CoatingCategory(name=category_name)
                db.session.add(category)
                db.session.flush()  # To get the category_id before committing

            # Process each image file inside the category's folder
            for file_name in os.listdir(category_path):
                file_path = os.path.join(category_path, file_name)
                if file_name.endswith((".png", ".jpg", ".jpeg")):
                    with open(file_path, "rb") as file:
                        file_content = file.read()
                        base64_data = base64.b64encode(file_content).decode("utf-8")

                        # Save the image to the database
                        new_image = Image(
                            name=secure_filename(file_name),
                            base64_data=base64_data,
                            category_id=category.id,
                        )
                        db.session.add(new_image)

    db.session.commit()

    # Clean up the temporary directory
    shutil.rmtree(temp_dir)

    return (
        jsonify({"message": "Coating categories and images uploaded successfully"}),
        201,
    )


### SHAPE ROUTES ###


@shape_blueprint.route("/", methods=["GET"])
def get_all_shapes():
    """
    Get all shapes
    """
    shapes = Shape.query.all()
    return jsonify([shape.simple_serialize() for shape in shapes]), 200


@shape_blueprint.route("/<int:shape_id>", methods=["GET"])
def get_shape(shape_id):
    """
    Get a shape by ID
    """
    shape = Shape.query.get(shape_id)
    if shape:
        return jsonify(shape.serialize()), 200
    return failure_response("Shape not found", 404)


@shape_blueprint.route("/", methods=["POST"])
def create_shape():
    """
    Create a new shape
    """
    data = request.json
    name = data.get("name")

    if name == None:
        return failure_response("Missing name", 400)

    new_shape = Shape(name=name)
    db.session.add(new_shape)
    db.session.commit()

    return success_response(new_shape.serialize(), 201)


@shape_blueprint.route("/<int:shape_id>/images", methods=["POST"])
def upload_shape_image(shape_id):
    """
    Upload an image for a shape as a base64 string
    """
    shape = Shape.query.get(shape_id)
    if shape is None:
        return jsonify({"error": "Shape not found"}), 404

    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Read the file and encode it to base64
    file_content = file.read()
    base64_data = base64.b64encode(file_content).decode("utf-8")

    # Save the image to the database
    new_image = Image(
        name=secure_filename(file.filename), base64_data=base64_data, shape_id=shape_id
    )
    db.session.add(new_image)
    db.session.commit()

    return jsonify(new_image.serialize()), 201


@shape_blueprint.route("/upload_zip", methods=["POST"])
def upload_shapes_from_zip():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    zip_file = request.files["file"]
    if not zip_file.filename.endswith(".zip"):
        return jsonify({"error": "The file must be a zip"}), 400

    # Unzip the file into a temporary directory
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(io.BytesIO(zip_file.read())) as z:
        z.extractall(temp_dir)

    # Process each directory in the first level directory of the extracted folder
    first_level_directory = next(os.walk(temp_dir))[1][0]
    shape_dir = os.path.join(temp_dir, first_level_directory)

    for shape_name in os.listdir(shape_dir):
        if shape_name == "__MACOSX":
            continue
        shape_path = os.path.join(shape_dir, shape_name)
        if os.path.isdir(shape_path):
            # Create a new shape for each folder
            new_shape = Shape(name=shape_name)
            db.session.add(new_shape)
            db.session.flush()  # To get the shape_id before committing

            # Process each image file inside the shape's folder
            for file_name in os.listdir(shape_path):
                file_path = os.path.join(shape_path, file_name)
                if file_name.endswith((".png", ".jpg", ".jpeg")):
                    with open(file_path, "rb") as file:
                        file_content = file.read()
                        base64_data = base64.b64encode(file_content).decode("utf-8")

                        # Save the image to the database
                        new_image = Image(
                            name=secure_filename(file_name),
                            base64_data=base64_data,
                            shape_id=new_shape.id,
                        )
                        db.session.add(new_image)

    db.session.commit()

    # Clean up the temporary directory
    shutil.rmtree(temp_dir)

    return jsonify({"message": "Shapes and images uploaded successfully"}), 201


### MATERIAL ROUTES ###
@material_blueprint.route("/categories", methods=["GET"])
def get_material_categories():
    """
    Get all material categories
    """
    categories = MaterialCategory.query.all()
    return success_response([category.simple_serialize() for category in categories])


@material_blueprint.route("/categories", methods=["POST"])
def create_material_category():
    """
    Create a new material category
    """
    data = request.json
    name = data.get("name")
    is_rare_earth = data.get("is_rare_earth")

    if name is None and is_rare_earth is None:
        return failure_response("Missing name or is_rare_earth", 400)

    new_category = MaterialCategory(name=name, is_rare_earth=is_rare_earth)
    db.session.add(new_category)
    db.session.commit()

    return success_response(new_category.serialize(), 201)


@material_blueprint.route("/categories/<int:category_id>", methods=["GET"])
def get_material_category(category_id):
    """
    Get a material category by ID
    """
    category = MaterialCategory.query.get(category_id)
    if category:
        return success_response(category.serialize())
    return failure_response("Category not found", 404)


@material_blueprint.route("/", methods=["GET"])
def get_all_materials():
    """
    Get all materials
    """
    materials = Material.query.all()
    return success_response([material.simple_serialize() for material in materials])


@material_blueprint.route("/<int:material_id>", methods=["GET"])
def get_material(material_id):
    """
    Get a material by ID
    """
    material = Material.query.get(material_id)
    if material:
        return success_response(material.serialize())
    return failure_response("Material not found", 404)


@material_blueprint.route("/", methods=["POST"])
def create_material():
    """
    Create a new material
    """
    data = request.json
    grade = data.get("grade")
    br_t = data.get("br_t")
    hcb_kA_m = data.get("hcb_kA_m")
    bh_max_kj_m3 = data.get("bh_max_kj_m3")
    category_id = data.get("category_id")

    if None in [grade, br_t, hcb_kA_m, bh_max_kj_m3, category_id]:
        return jsonify({"error": "Missing required material properties"}), 400

    new_material = Material(
        grade=grade,
        br_t=br_t,
        hcb_kA_m=hcb_kA_m,
        bh_max_kj_m3=bh_max_kj_m3,
        category_id=category_id,
    )
    db.session.add(new_material)
    db.session.commit()
    return success_response(new_material.serialize(), 201)


@material_blueprint.route("/upload_zip", methods=["POST"])
def upload_materials_from_zip():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    zip_file = request.files["file"]
    if not zip_file.filename.endswith(".zip"):
        return jsonify({"error": "The file must be a zip"}), 400

    # Create a temporary directory to extract the zip
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(io.BytesIO(zip_file.read())) as z:
        z.extractall(temp_dir)

    # Process each directory in the first level directory of the extracted folder
    first_level_directory = next(os.walk(temp_dir))[1][0]
    material_dir = os.path.join(temp_dir, first_level_directory)

    try:
        with zipfile.ZipFile(zip_file) as z:
            z.extractall(material_dir)

        # Process each directory in the extracted folder
        for folder_name in os.listdir(material_dir):
            folder_path = os.path.join(material_dir, folder_name)
            if os.path.isdir(folder_path):
                is_rare_earth = not ("Non Rare Earth" in folder_name)
                process_material_folder(folder_path, is_rare_earth)
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir)

    return jsonify({"message": "Materials uploaded successfully"}), 201


def process_material_folder(folder_path, is_rare_earth):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(file_path)
            df.columns = df.columns.str.lower().str.replace(" ", "")

            category_name = os.path.splitext(filename)[0]
            category = MaterialCategory.query.filter_by(name=category_name).first()
            if not category:
                category = MaterialCategory(
                    name=category_name, is_rare_earth=is_rare_earth
                )
                db.session.add(category)
                db.session.flush()  # Get the category_id before committing

            for _, row in df.iterrows():
                material = Material(
                    grade=row["grade"],
                    br_t=row["br_t"],
                    hcb_kA_m=row["hcb_ka/m"],
                    bh_max_kj_m3=row["bh_max_kj/m3"],
                    category_id=category.id,
                )
                db.session.add(material)

            db.session.commit()
