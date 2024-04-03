from flask import request, jsonify, Blueprint, current_app
import pandas as pd
from werkzeug.utils import secure_filename
from app import db
from app.models import User, Coating, CoatingCategory, Shape, Image
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
    df = pd.read_excel(filepath, engine='openpyxl')
    
    # Standardize column headers: lower case and replace spaces with underscores
    df.columns = df.columns.str.lower().str.replace(' ', '')
    
    return df

def allowed_file_excel(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'xlsx', 'xls'}


### BLUEPRINTS ###

user_blueprint = Blueprint('user_blueprint', __name__)
coating_blueprint = Blueprint('coating_blueprint', __name__)
shape_blueprint = Blueprint('shape_blueprint', __name__)


### USER ROUTES ###

@user_blueprint.route('/', methods=['POST'])
def create_user():
    """
    Create a new user
    """
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return failure_response("Missing username or password", 400)

    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()

    return success_response(new_user.serialize(), 201)

@user_blueprint.route('/', methods=['GET'])
def get_users():
    """
    Get all users
    """
    users = User.query.all()
    return success_response([user.serialize() for user in users])


### COATING ROUTES ###

@coating_blueprint.route('/categories', methods=['GET'])
def get_all_coating_categories():
    """
    Get all coating categories
    """
    categories = CoatingCategory.query.all()
    return success_response([category.simple_serialize() for category in categories])

@coating_blueprint.route('/categories', methods=['POST'])
def create_coating_category():
    """
    Create a new coating category
    """
    data = request.json
    name = data.get('name')

    if not name:
        return failure_response("Missing name", 400)

    new_category = CoatingCategory(name=name)
    db.session.add(new_category)
    db.session.commit()

    return success_response(new_category.serialize(), 201)

@coating_blueprint.route('/categories/<int:category_id>', methods=['GET'])
def get_coating_category(category_id):
    """
    Get a coating category by ID
    """
    category = CoatingCategory.query.get(category_id)
    if category:
        return success_response(category.serialize())
    return failure_response("Category not found", 404)

@coating_blueprint.route('/', methods=['GET'])
def get_all_coatings():
    """
    Get all coatings
    """
    coatings = Coating.query.all()
    return success_response([coating.serialize() for coating in coatings])

@coating_blueprint.route('/<int:coating_id>', methods=['GET'])
def get_coating(coating_id):
    """
    Get a coating by ID
    """
    coating = Coating.query.get(coating_id)
    if coating:
        return success_response(coating.serialize())
    return failure_response("Coating not found", 404)

@coating_blueprint.route('/', methods=['POST'])
def create_coating():
    """
    Create a new coating
    """
    data = request.json
    name = data.get('name')
    sub_category = data.get('sub_category')
    thickness = data.get('thickness')
    color = data.get('color')

    if not name or not sub_category or not thickness or not color:
        return failure_response("Missing required fields", 400)

    new_coating = Coating(name=name, sub_category=sub_category, thickness=thickness, color=color)
    db.session.add(new_coating)
    db.session.commit()

    return success_response(new_coating.serialize(), 201)

@coating_blueprint.route('/upload_excel', methods=['POST'])
def upload_coatings():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    file_extension = os.path.splitext(file.filename)[1]

    if file_extension.lower() == '.xls':
        df = pd.read_excel(file, engine='xlrd')
    elif file_extension.lower() == '.xlsx':
        df = pd.read_excel(file, engine='openpyxl')
    else:
        return jsonify({'error': 'Invalid file format'}), 400

    df.columns = df.columns.str.lower().str.replace(' ', '')

    for index, row in df.iterrows():
        # Check and create CoatingCategory if needed
        category_name = row['category']
        category = CoatingCategory.query.filter_by(name=category_name).first()
        if not category:
            category = CoatingCategory(name=category_name)
            db.session.add(category)
            db.session.flush()  # To get the category_id before committing

        # Create a new Coating
        new_coating = Coating(sub_category=row['subcategory'],
                              thickness=row['thickness'], color=row['color'], category_id=category.id)
        db.session.add(new_coating)

    db.session.commit()
    return jsonify({'message': 'Coatings uploaded successfully'}), 201

@coating_blueprint.route('/categories/upload_zip', methods=['POST'])
def upload_categories_from_zip():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    zip_file = request.files['file']
    if not zip_file.filename.endswith('.zip'):
        return jsonify({'error': 'The file must be a zip'}), 400

    # Unzip the file into a temporary directory
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(io.BytesIO(zip_file.read())) as z:
        z.extractall(temp_dir)

    # Process each directory in the first level directory of the extracted folder
    first_level_directory = next(os.walk(temp_dir))[1][0]
    category_dir = os.path.join(temp_dir, first_level_directory)

    for category_name in os.listdir(category_dir):
        if category_name == '__MACOSX':
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
                if file_name.endswith(('.png', '.jpg', '.jpeg')):
                    with open(file_path, 'rb') as file:
                        file_content = file.read()
                        base64_data = base64.b64encode(file_content).decode('utf-8')

                        # Save the image to the database
                        new_image = Image(name=secure_filename(file_name), 
                                          base64_data=base64_data, 
                                          category_id=category.id)
                        db.session.add(new_image)

    db.session.commit()

    # Clean up the temporary directory
    shutil.rmtree(temp_dir)

    return jsonify({'message': 'Coating categories and images uploaded successfully'}), 201


### SHAPE ROUTES ###

@shape_blueprint.route('/', methods=['GET'])
def get_all_shapes():
    """
    Get all shapes
    """
    shapes = Shape.query.all()
    return jsonify([shape.simple_serialize() for shape in shapes]), 200

@shape_blueprint.route('/<int:shape_id>', methods=['GET'])
def get_shape(shape_id):
    """
    Get a shape by ID
    """
    shape = Shape.query.get(shape_id)
    if shape:
        return jsonify(shape.serialize()), 200
    return failure_response("Shape not found", 404)

@shape_blueprint.route('/', methods=['POST'])
def create_shape():
    """
    Create a new shape
    """
    data = request.json
    name = data.get('name')

    if name == None:
        return failure_response("Missing name", 400)

    new_shape = Shape(name=name)
    db.session.add(new_shape)
    db.session.commit()

    return success_response(new_shape.serialize(), 201)

@shape_blueprint.route('/<int:shape_id>/images', methods=['POST'])
def upload_shape_image(shape_id):
    """
    Upload an image for a shape as a base64 string
    """
    shape = Shape.query.get(shape_id)
    if shape is None:
        return jsonify({"error": "Shape not found"}), 404

    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Read the file and encode it to base64
    file_content = file.read()
    base64_data = base64.b64encode(file_content).decode('utf-8')

    # Save the image to the database
    new_image = Image(name=secure_filename(file.filename), base64_data=base64_data, shape_id=shape_id)
    db.session.add(new_image)
    db.session.commit()

    return jsonify(new_image.serialize()), 201

import os

@shape_blueprint.route('/upload_zip', methods=['POST'])
def upload_shapes_from_zip():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    zip_file = request.files['file']
    if not zip_file.filename.endswith('.zip'):
        return jsonify({'error': 'The file must be a zip'}), 400

    # Unzip the file into a temporary directory
    temp_dir = tempfile.mkdtemp()
    with zipfile.ZipFile(io.BytesIO(zip_file.read())) as z:
        z.extractall(temp_dir)

    # Process each directory in the first level directory of the extracted folder
    first_level_directory = next(os.walk(temp_dir))[1][0]
    shape_dir = os.path.join(temp_dir, first_level_directory)

    for shape_name in os.listdir(shape_dir):
        if shape_name == '__MACOSX':
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
                if file_name.endswith(('.png', '.jpg', '.jpeg')):
                    with open(file_path, 'rb') as file:
                        file_content = file.read()
                        base64_data = base64.b64encode(file_content).decode('utf-8')

                        # Save the image to the database
                        new_image = Image(name=secure_filename(file_name), base64_data=base64_data, shape_id=new_shape.id)
                        db.session.add(new_image)

    db.session.commit()

    # Clean up the temporary directory
    shutil.rmtree(temp_dir)

    return jsonify({'message': 'Shapes and images uploaded successfully'}), 201