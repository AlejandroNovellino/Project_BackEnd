"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for, json
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from flask_jwt_extended import create_access_token, JWTManager
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Common_data, Professor, Cathedra, Cathedra_asigns, Student, Professor_student_rel, Course, Notes, Evaluation_plan, Evaluation
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["JWT_SECRET_KEY"] = "01cdeef14f0a17d28d723f35a2ba3670"
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)
jwt = JWTManager(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route("/sign-up", methods=["POST"])
def sign_up():
    data = request.json
    user = User.create(email=data.get('email'), password=data.get('password'), role=data.get('role'))
    if not isinstance(user, User):
        return jsonify({"msg": "Ocurrio un problema interno"}), 500
    return jsonify(user.serialize()), 201

@app.route("/log-in", methods=["POST"])
def log_in():
    print(request.data)
    print(request.json)
    data = request.json
    user = User.query.filter_by(email=data['email']).one_or_none()

    if user is None: 
        return jsonify({"msg": "No existe el usuario"}), 404
    if not user.check_password(data.get('password')):
        return jsonify({"msg": "Credenciales incorrectas"}), 400

    token = create_access_token(identity=user.id)

    return jsonify({
        "user": user.serialize(),
        "token": token
    }), 200

@app.route("/cathedra", methods=["GET"])
def get_all_cathedras():
    '''

    '''
    cathedras = [cathedra.serialized() for cathedra in Cathedra.query.all()]
    return jsonify({cathedras}), 200

@app.route("/only-cathedra", methods=["POST"])
def create_cathedra():
    '''
    '''
    data = json.loads(request.data)
    new_cathedra = Cathedra(
        name=data["name"],
        credits=data["credits"],
        career=data["career"]
    )

    db.session.add(new_cathedra)
    try:
        db.session.commit()
    except:
        db.session.rollback()
        return jsonify({"msg": "Hubo un error creando la materia"}), 500

    return jsonify(new_cathedra.serialize_only_cathedra()), 200


# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 4000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
