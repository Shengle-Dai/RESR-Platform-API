from flask import request, jsonify, Blueprint
from app import db
from app.models import User

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


# Blueprint setup for user routes
user_blueprint = Blueprint('user_blueprint', __name__)

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