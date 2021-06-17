"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from openpyxl import load_workbook

from flask import Flask, request, jsonify, url_for, json
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from flask_jwt_extended import create_access_token, JWTManager
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Common_data, Professor, Cathedra, Cathedra_asigns, Student, Course, Inscription, Grade, Evaluation, Career

#UPLOAD_FOLDER = '/files'

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["JWT_SECRET_KEY"] = "01cdeef14f0a17d28d723f35a2ba3670"
app.config['UPLOAD_FOLDER'] = '/files'

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

# endpoint for getting the possibles career
@app.route("/get-careers", methods=["GET"])
def get_all_careers():
    '''
        Get all careers
    '''
    careers = []
    for career in Career:
        careers.append(career.name)

    return jsonify(careers), 200

# endpoints for cathedra
@app.route("/cathedra", methods=["GET"])
def get_all_cathedras():
    '''
        Get all cathedras
    '''
    cathedras = [cathedra.serialize() for cathedra in Cathedra.query.all()]
    return jsonify([cathedra.serialize_when_created() for cathedra in cathedras]), 200

@app.route("/cathedra", methods=["POST"])
def create_cathedra():
    '''
        Creates a new cathedra with just "name, code, credits, career"
    '''
    data = json.loads(request.data)
    new_cathedra = Cathedra(
        name=data["name"],
        code=data["code"],
        credits=data["credits"],
        career=data["career"]
    )

    db.session.add(new_cathedra)
    try:
        db.session.commit()
    except:
        db.session.rollback()
        return jsonify({"msg": "Hubo un error creando la materia"}), 500

    return jsonify(new_cathedra.serialize_when_created()), 200

# endpoints for professor
@app.route("/professor", methods=["POST"])
def create_professor():
    '''
        Creates a new professor
    '''
    # creates the professor 
    data = json.loads(request.data)
    new_professor = Professor(
        full_name=data["fullName"],
        ci=data["ci"],
        phone_number=data["phoneNumber"],
        age=data["age"],
        nationality=data["nationality"],
        residence=data["residence"],
        career=data["career"]
    )
    db.session.add(new_professor)
    try:
        db.session.commit()
    except:
        db.session.rollback()
        return jsonify({"msg": "Hubo un error creando al profesor"}), 500

    # creates the relations with the cathedras
    for cathedra_code in data["cathedras"]:
        cathedra = Cathedra.query.filter_by(code=cathedra_code)
        new_relation = Cathedra_asigns(professor_id=new_professor.id, cathedra_id=cathedra[0].id)
        db.session.add(new_relation)

    try:
        db.session.commit()
    except:
        db.session.rollback()
        return jsonify({"msg": "Hubo un error creando las relaciones"}), 500

    return jsonify(new_professor.serialize_when_created()), 200

# endpoints for student
@app.route("/upload-students", methods=["POST"])
def upload_file():
    '''
        Upload the data of a file
    '''

    myFile = request.files["myFile"]

    # wb = workbook 
    wb = load_workbook(myFile)
    sheet_name = wb.sheetnames[0]
    # ws = worksheet
    ws = wb[sheet_name]
    # the ws is a dictionary but the rows are tuples

    for row in ws.iter_rows(min_row=2):
        new_student = Student(
            full_name=row[0].value,
            ci=row[1].value,
            phone_number=row[2].value,
            age=row[3].value,
            nationality=row[4].value,
            residence=row[5].value,
            career=row[6].value
        )
        db.session.add(new_student)
        print(new_student)

    try:
        db.session.commit()
    except:
        db.session.rollback()
        return jsonify({"msg": "Hubo un problema creando al estudiante"}), 500

    return jsonify({"msg": "Se anadireron los estudiantes del archivo"}), 200


# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 4000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
