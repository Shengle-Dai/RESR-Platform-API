from flask import request, jsonify, Blueprint, current_app
import pandas as pd
from werkzeug.utils import secure_filename
from app import db
from app.models import User, MaterialMainCategory, MaterialSubCategory, Material
import os


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

def load_data_to_database(df):
    for index, row in df.iterrows():
        main_category_name = row['maincategory']
        sub_category_name = row['subcategory']
        material_name = row['material']

        # Find or create the main category
        main_category = MaterialMainCategory.query.filter_by(name=main_category_name).first()
        if not main_category:
            main_category = MaterialMainCategory(name=main_category_name)
            db.session.add(main_category)
            db.session.commit()  # Commit to obtain the main category ID

        # Find or create the sub category
        sub_category = MaterialSubCategory.query.filter_by(name=sub_category_name, material_main_category_id=main_category.id).first()
        if not sub_category:
            sub_category = MaterialSubCategory(name=sub_category_name, material_main_category_id=main_category.id)
            db.session.add(sub_category)
            db.session.commit()  # Commit to obtain the sub category ID

        # Find or create the material
        material = Material.query.filter_by(name=material_name, material_sub_category_id=sub_category.id).first()
        if not material:
            material = Material(name=material_name, material_sub_category_id=sub_category.id)
            db.session.add(material)
        
        # Batch commit: Commit after every 10 records
        if index % 10 == 0:
            db.session.commit()

    db.session.commit()  # Commit any remaining records


### BLUEPRINTS ###

user_blueprint = Blueprint('user_blueprint', __name__)
material_blueprint = Blueprint('material_blueprint', __name__)


### USER ROUTES ###

@user_blueprint.route('/users', methods=['POST'])
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

@user_blueprint.route('/users', methods=['GET'])
def get_users():
    """
    Get all users
    """
    users = User.query.all()
    return success_response([user.serialize() for user in users])


### MATERIAL ROUTES ###

@material_blueprint.route('/upload-materials', methods=['POST'])
def upload_materials():
    # Check if a file is in the request
    if 'file' not in request.files:
        return failure_response('No file part in the request', 400)

    file = request.files['file']

    # If user does not select file, browser also submits an empty part without filename
    if file.filename == '':
        return failure_response('No selected file', 400)

    # Check if file has allowed extension (you may define a function for this)
    if not file or not allowed_file_excel(file.filename):
        return failure_response('Invalid file type', 400)

    # Make filename safe, remove unsupported chars
    filename = secure_filename(file.filename)
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    # Process the uploaded file
    try:
        df = process_excel_file(filepath)
        load_data_to_database(df)
    except Exception as e:
        return failure_response(f"An error occurred: {str(e)}", 500)
    finally:
        # Clean up the uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)

    return success_response(f"File {filename} uploaded and processed successfully", 201)

@material_blueprint.route('/materials', methods=['GET'])
def get_all_materials():
    materials = Material.query.all()
    return jsonify([material.serialize() for material in materials]), 200

@material_blueprint.route('/subcategories', methods=['GET'])
def get_all_subcategories():
    subcategories = MaterialSubCategory.query.all()
    return jsonify([subcategory.serialize() for subcategory in subcategories]), 200

@material_blueprint.route('/maincategories', methods=['GET'])
def get_all_main_categories():
    main_categories = MaterialMainCategory.query.all()
    return jsonify([main_category.serialize() for main_category in main_categories]), 200
