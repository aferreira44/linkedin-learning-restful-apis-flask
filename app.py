import os
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'planets.db')
app.config['JWT_SECRET_KEY'] = 'super-secret'

app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)


@app.cli.command('db_create')
def db_create():
    db.create_all()
    print('Database created!')


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print('Database dropped!')


@app.cli.command('db_seed')
def db_seed():
    mercury = Planet(planet_name='Mercury',
                     planet_type='Class D',
                     home_star='Sun',
                     mass=3.258e23,
                     radius=1516,
                     distance=35.98e6)

    venus = Planet(planet_name='Venus',
                   planet_type='Class K',
                   home_star='Sun',
                   mass=3.258e23,
                   radius=1516,
                   distance=35.98e6)

    earth = Planet(planet_name='Earth',
                   planet_type='Class M',
                   home_star='Sun',
                   mass=3.258e23,
                   radius=1516,
                   distance=35.98e6)

    db.session.add(mercury)
    db.session.add(venus)
    db.session.add(earth)

    test_user = User(first_name='William', last_name='Herschel', email='test@test.com', password='password')

    db.session.add(test_user)
    db.session.commit()

    print('Database seeded!')


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/super_simple')
def super_simple():
    return jsonify(message='Hello, from the Planetary API.')


@app.route('/not_found')
def not_found():
    return jsonify(message='The resource was not found'), 404


@app.route('/parameters')
def parameters():
    name = request.args.get('name')
    age = int(request.args.get('age'))

    if age < 18:
        return jsonify(message="Sorry {0}, you're not old enough.".format(name)), 401
    else:
        return jsonify(message="Welcome {0}, you're old enough.".format(name))


@app.route('/url_variables/<string:name>/<int:age>')
def url_variable(name: str, age: int):
    if age < 18:
        return jsonify(message="Sorry {0}, you're not old enough.".format(name)), 401
    else:
        return jsonify(message="Welcome {0}, you're old enough.".format(name))


@app.route('/planets', methods=['GET'])
def all_planets():
    planets_list = Planet.query.all()
    return jsonify(planets_schema.dump(planets_list))


@app.route('/planets/<int:planet_id>', methods=['GET'])
def read_planet(planet_id: int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        return jsonify(planet_schema.dump(planet))
    else:
        return jsonify(message="That planet does not exist."), 404


@app.route('/planets', methods=['POST'])
@jwt_required
def create_planet():
    planet_name = request.json['planet_name']
    planet = Planet.query.filter_by(planet_name=planet_name).first()
    if planet:
        return jsonify(message="That planet already exists."), 500
    else:
        planet_type = request.json['planet_type']
        if not planet_type:
            return jsonify(message="{0} is empty".format('planet_type')), 500

        home_star = request.json['home_star']
        if not home_star:
            return jsonify(message="{0} is empty".format('home_star')), 500

        mass = float(request.json['mass'])
        if not mass:
            return jsonify(message="{0} is empty".format('mass')), 500

        radius = float(request.json['radius'])
        if not radius:
            return jsonify(message="{0} is empty".format('radius')), 500

        distance = float(request.json['distance'])
        if not distance:
            return jsonify(message="{0} is empty".format('distance')), 500

    planet = Planet(planet_name=planet_name,
                    planet_type=planet_type,
                    home_star=home_star,
                    mass=mass,
                    radius=radius,
                    distance=distance)

    db.session.add(planet)
    db.session.commit()

    return jsonify(planet_schema.dump(planet)), 201


@jwt_required
@app.route('/planets/<int:planet_id>', methods=['PUT'])
def update_planet(planet_id: int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        if not request.json['planet_name']:
            return jsonify(message="{0} is empty".format('planet_type')), 500
        else:
            planet_name_exists = Planet.query.filter_by(planet_name=request.json['planet_name']).first()

            if planet_name_exists:
                return jsonify(message="That planet already exists."), 500

        if not request.json['planet_type']:
            return jsonify(message="{0} is empty".format('planet_type')), 500
        if not request.json['home_star']:
            return jsonify(message="{0} is empty".format('home_star')), 500
        if not request.json['mass']:
            return jsonify(message="{0} is empty".format('mass')), 500
        if not request.json['radius']:
            return jsonify(message="{0} is empty".format('radius')), 500
        if not request.json['distance']:
            return jsonify(message="{0} is empty".format('distance')), 500

        planet.planet_name = request.json['planet_name']
        planet.planet_type = request.json['planet_type']
        planet.home_star = request.json['home_star']
        planet.mass = float(request.json['mass'])
        planet.radius = float(request.json['radius'])
        planet.distance = float(request.json['distance'])

        db.session.commit()

        return jsonify(planet_schema.dump(planet)), 202
    else:
        return jsonify(message="That planet does not exist."), 404


@jwt_required
@app.route('/planets/<int:planet_id>', methods=['DELETE'])
def delete_planet(planet_id: int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        db.session.delete(planet)
        db.session.commit()
        return jsonify(message="You delete a planet"), 202
    else:
        return jsonify(message="That planet does not exist."), 404


@app.route('/register', methods=['POST'])
def register():
    email = request.json['email']
    user = User.query.filter_by(email=email).first()

    if user:
        return jsonify(message='That email already exists.'), 409
    else:
        first_name = request.json['first_name']
        last_name = request.json['last_name']
        password = request.json['password']

        user = User(first_name=first_name, last_name=last_name, email=email, password=password)

        db.session.add(user)
        db.session.commit()

        return jsonify(message="User created successfully."), 201


@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.json['email']
        password = request.json['password']

    user = User.query.filter_by(email=email, password=password).first()

    if user:
        access_token = create_access_token(identity=email)
        return jsonify(message='Login succeeded.', access_token=access_token)
    else:
        return jsonify(message='Bad email or password.'), 401


@app.route('/retrieve_password/<string:email>', methods=['GET'])
def retrieve_password(email: str):
    user = User.query.filter_by(email=email).first()
    if user:
        msg = Message('Your Planetary API password is {0}'.format(user.password), sender='admin@planetary-api.com',
                      recipients=[email])
        mail.send(msg)

        return jsonify(message="Password sent to {0}".format(email))
    else:
        return jsonify(message="That email doesn't exist")


# database models
class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class Planet(db.Model):
    __tablename__ = 'planets'
    planet_id = Column(Integer, primary_key=True)
    planet_name = Column(String)
    planet_type = Column(String)
    home_star = Column(String)
    mass = Column(Float)
    radius = Column(Float)
    distance = Column(Float)


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'password')


class PlanetSchema(ma.Schema):
    class Meta:
        fields = ('planet_id', 'planet_name', 'planet_type', 'home_star', 'mass', 'radius', 'distance')


user_schema = UserSchema()
users_schema = UserSchema(many=True)

planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)

if __name__ == '__main__':
    app.run()
