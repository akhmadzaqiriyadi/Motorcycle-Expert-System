from flask import request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from functools import wraps
from . import db
from .models import Motorcycle, Damage, Symptom, Cause, Solution, Rule, RuleSymptom, User, Consultation, ConsultationSymptom
from .expert_system import ForwardChainingEngine

# Initialize expert system engine
expert_system = ForwardChainingEngine()

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.filter_by(id=data['user_id']).first()
            if not current_user:
                return jsonify({'message': 'User not found!'}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({'message': f'Token is invalid: {str(e)}!'}), 401
            
        return f(current_user, *args, **kwargs)
    
    return decorated

def init_routes(app):
    # Routes
    @app.route('/api/login', methods=['POST'])
    def login():
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'message': 'Missing credentials'}), 400
            
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not check_password_hash(user.password, data['password']):
            return jsonify({'message': 'Invalid credentials'}), 401
            
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(hours=24)
        }, app.config['SECRET_KEY'])
        
        return jsonify({
            'token': token,
            'user': user.to_dict()
        })

    @app.route('/api/register', methods=['POST'])
    def register():
        data = request.get_json()
        
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'message': 'Missing data'}), 400
            
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'message': 'Username already exists'}), 400
            
        hashed_password = generate_password_hash(data['password'])
        new_user = User(
            username=data['username'],
            password=hashed_password,
            role=data.get('role', 'user')
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({'message': 'User created successfully'}), 201

    @app.route('/api/motorcycles', methods=['GET'])
    def get_motorcycles():
        motorcycles = Motorcycle.query.all()
        return jsonify([m.to_dict() for m in motorcycles])

    @app.route('/api/motorcycles', methods=['POST'])
    @token_required
    def add_motorcycle(current_user):
        if current_user.role != 'admin':
            return jsonify({'message': 'Permission denied'}), 403
            
        data = request.get_json()
        
        if not data or not data.get('brand') or not data.get('model'):
            return jsonify({'message': 'Missing data'}), 400
            
        new_motorcycle = Motorcycle(
            brand=data['brand'],
            model=data['model']
        )
        
        db.session.add(new_motorcycle)
        db.session.commit()
        
        return jsonify(new_motorcycle.to_dict()), 201

    @app.route('/api/symptoms', methods=['GET'])
    def get_symptoms():
        symptoms = Symptom.query.all()
        return jsonify([s.to_dict() for s in symptoms])

    @app.route('/api/symptoms', methods=['POST'])
    @token_required
    def add_symptom(current_user):
        if current_user.role != 'admin':
            return jsonify({'message': 'Permission denied'}), 403
            
        data = request.get_json()
        
        if not data or not data.get('code') or not data.get('name'):
            return jsonify({'message': 'Missing data'}), 400
            
        new_symptom = Symptom(
            code=data['code'],
            name=data['name'],
            description=data.get('description', '')
        )
        
        db.session.add(new_symptom)
        db.session.commit()
        
        return jsonify(new_symptom.to_dict()), 201

    @app.route('/api/damages', methods=['GET'])
    def get_damages():
        damages = Damage.query.all()
        return jsonify([d.to_dict() for d in damages])

    @app.route('/api/damages', methods=['POST'])
    @token_required
    def add_damage(current_user):
        if current_user.role != 'admin':
            return jsonify({'message': 'Permission denied'}), 403
            
        data = request.get_json()
        
        if not data or not data.get('code') or not data.get('name'):
            return jsonify({'message': 'Missing data'}), 400
            
        new_damage = Damage(
            code=data['code'],
            name=data['name'],
            description=data.get('description', '')
        )
        
        db.session.add(new_damage)
        db.session.commit()
        
        return jsonify(new_damage.to_dict()), 201

    @app.route('/api/rules', methods=['GET'])
    def get_rules():
        rules = Rule.query.all()
        return jsonify([r.to_dict() for r in rules])

    @app.route('/api/rules', methods=['POST'])
    @token_required
    def add_rule(current_user):
        if current_user.role != 'admin':
            return jsonify({'message': 'Permission denied'}), 403
            
        data = request.get_json()
        
        if not data or not data.get('damage_id') or not data.get('symptom_ids'):
            return jsonify({'message': 'Missing data'}), 400
            
        new_rule = Rule(damage_id=data['damage_id'])
        db.session.add(new_rule)
        db.session.flush()
        
        for symptom_id in data['symptom_ids']:
            rule_symptom = RuleSymptom(rule_id=new_rule.id, symptom_id=symptom_id)
            db.session.add(rule_symptom)
        
        db.session.commit()
        
        return jsonify(new_rule.to_dict()), 201

    @app.route('/api/diagnose', methods=['POST'])
    def diagnose():
        data = request.get_json()
        
        if not data or not data.get('symptom_ids') or not data.get('motorcycle_id'):
            return jsonify({'message': 'Missing data'}), 400
            
        symptom_ids = data['symptom_ids']
        motorcycle_id = data['motorcycle_id']
        
        diagnosis = expert_system.diagnose(symptom_ids)
        
        new_consultation = Consultation(
            user_id=data.get('user_id'),
            motorcycle_id=motorcycle_id,
            damage_id=diagnosis['id'] if diagnosis else None
        )
        db.session.add(new_consultation)
        db.session.flush()
        
        for symptom_id in symptom_ids:
            cs = ConsultationSymptom(consultation_id=new_consultation.id, symptom_id=symptom_id)
            db.session.add(cs)
        
        db.session.commit()
        
        if diagnosis:
            return jsonify({
                'consultation_id': new_consultation.id,
                'diagnosis': diagnosis
            })
        else:
            return jsonify({
                'consultation_id': new_consultation.id,
                'diagnosis': None,
                'message': 'No matching diagnosis found'
            })

    @app.route('/api/consultations', methods=['GET'])
    @token_required
    def get_consultations(current_user):
        if current_user.role == 'admin':
            consultations = Consultation.query.all()
        else:
            consultations = Consultation.query.filter_by(user_id=current_user.id).all()
        
        return jsonify([c.to_dict() for c in consultations])

    @app.route('/api/seed', methods=['POST'])
    def seed_database():
        """Endpoint to seed the database with initial data (for development only)"""
        motorcycles = [
            {'brand': 'Honda', 'model': 'Beat'},
            {'brand': 'Honda', 'model': 'Vario'},
            {'brand': 'Yamaha', 'model': 'NMAX'},
            {'brand': 'Yamaha', 'model': 'Mio'}
        ]
        
        for moto_data in motorcycles:
            motorcycle = Motorcycle(**moto_data)
            db.session.add(motorcycle)
        
        symptoms = [
            {'code': 'G1', 'name': 'Motor Tidak Mau Bergerak'},
            {'code': 'G2', 'name': 'Mesin Menyala'},
            {'code': 'G3', 'name': 'Timbul Bunyi Berdecit'},
            {'code': 'G4', 'name': 'Lebar Drive Belt Kurang Dari Atau Sama Dengan 18,9mm'},
            {'code': 'G5', 'name': 'Bentuk Ramp Plate Tidak Sempurna'},
            {'code': 'G6', 'name': 'Driven Face Tidak Menekan Drive Belt'},
            {'code': 'G7', 'name': 'Drive Belt Terlepas Dari Pully'},
            {'code': 'G8', 'name': 'Tenaga Motor Kurang'},
            {'code': 'G9', 'name': 'Timbul Bau Karet Terbakar'},
            {'code': 'G10', 'name': 'Permukaan Pully Berminyak'},
            {'code': 'G11', 'name': 'Saat Digas Tinggi Kemudian Dilepas, Muncul Suara Benturan Dari CVT'},
            {'code': 'G12', 'name': 'Driven Face Lemah Saat Ditekan'},
            {'code': 'G13', 'name': 'Panjang Pegas Driven Face < 99,8mm'},
            {'code': 'G14', 'name': 'Moveable Driven Face Seret Saat Digerakkan'},
            {'code': 'G15', 'name': 'Weight Roller Tidak Silinder Lagi'},
            {'code': 'G16', 'name': 'Tarikan Motor Menghentak-hentak'},
            {'code': 'G17', 'name': 'Permukaan Drive Face Tidak Rata'},
            {'code': 'G18', 'name': 'Warna Clutch Outter Biru Gelap'},
            {'code': 'G19', 'name': 'Diameter Dalam Clucth Outer Kurang Dari Atau Sama Dengan 125,5mm'},
            {'code': 'G20', 'name': 'Motor Habis Terkena Banjir'},
            {'code': 'G21', 'name': 'Terdapat Air Pada Ruang CVT'},
            {'code': 'G22', 'name': 'Ketebalan Clucth Shoe Kurang Dari Atau Sama Dengan 2,5mm'},
            {'code': 'G23', 'name': 'Timbul Bunyi Ngorok Dari CVT'},
            {'code': 'G24', 'name': 'Filter Udara CVT Kotor'},
            {'code': 'G25', 'name': 'Ruang CVT Dipenuhi Debu / Kotoran'},
            {'code': 'G26', 'name': 'Mesin Mati Saat Langsam'},
            {'code': 'G27', 'name': 'Motor Berjalan Sendiri Walaupun Tidak Digas'},
            {'code': 'G28', 'name': 'Tenaga Motor Kurang Ditanjakan'},
            {'code': 'G29', 'name': 'Alur Torque Cam Menjadi Lebih Landai'}
        ]
        
        for symptom_data in symptoms:
            symptom = Symptom(**symptom_data)
            db.session.add(symptom)
        
        damages = [
            {'code': 'K1', 'name': 'Drive Belt Aus'},
            {'code': 'K2', 'name': 'Ramp Plate Rusak'},
            {'code': 'K3', 'name': 'Pegas Driven Face Patah Ringan'},
            {'code': 'K4', 'name': 'Drive Belt Putus'},
            {'code': 'K5', 'name': 'Drive Belt Terkontaminasi Minyak'},
            {'code': 'K6', 'name': 'Pegas Driven Face Lemah'},
            {'code': 'K7', 'name': 'Poros Moveable Driven Face Kurang Pelumas'},
            {'code': 'K8', 'name': 'Weight Roller Rusak'},
            {'code': 'K9', 'name': 'Drive Face Rusak'},
            {'code': 'K10', 'name': 'Cluth Outter Rusak'},
            {'code': 'K11', 'name': 'Cvt Kemasukan Air'},
            {'code': 'K12', 'name': 'Clucth Shoe Aus'},
            {'code': 'K13', 'name': 'Cvt Terkontaminasi Kotoran'},
            {'code': 'K14', 'name': 'Pegas Clucth Weight Patah'},
            {'code': 'K15', 'name': 'Torque Cam Rusak'}
        ]
        
        for damage_data in damages:
            damage = Damage(**damage_data)
            db.session.add(damage)
        
        admin_user = User(
            username='admin',
            password=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin_user)
        
        tech_user = User(
            username='technician',
            password=generate_password_hash('tech123'),
            role='technician'
        )
        db.session.add(tech_user)
        
        db.session.commit()
        
        rule1 = Rule(damage_id=1)  # K1: Drive Belt Aus
        db.session.add(rule1)
        db.session.flush()
        
        rule_symptom1 = RuleSymptom(rule_id=rule1.id, symptom_id=4)  # G4
        db.session.add(rule_symptom1)
        
        rule2 = Rule(damage_id=4)  # K4: Drive Belt Putus
        db.session.add(rule2)
        db.session.flush()
        
        rule_symptom2a = RuleSymptom(rule_id=rule2.id, symptom_id=1)  # G1
        rule_symptom2b = RuleSymptom(rule_id=rule2.id, symptom_id=2)  # G2
        rule_symptom2c = RuleSymptom(rule_id=rule2.id, symptom_id=7)  # G7
        db.session.add(rule_symptom2a)
        db.session.add(rule_symptom2b)
        db.session.add(rule_symptom2c)
        
        rule3 = Rule(damage_id=5)  # K5: Drive Belt Terkontaminasi Minyak
        db.session.add(rule3)
        db.session.flush()
        
        rule_symptom3a = RuleSymptom(rule_id=rule3.id, symptom_id=8)  # G8
        rule_symptom3b = RuleSymptom(rule_id=rule3.id, symptom_id=10)  # G10
        db.session.add(rule_symptom3a)
        db.session.add(rule_symptom3b)
        
        solutions = [
            {'damage_id': 1, 'description': 'Ganti drive belt dengan yang baru sesuai spesifikasi pabrikan.'},
            {'damage_id': 4, 'description': 'Ganti drive belt yang putus dengan yang baru.'},
            {'damage_id': 5, 'description': 'Bersihkan permukaan pully dari minyak dan ganti drive belt dengan yang baru.'}
        ]
        
        for solution_data in solutions:
            solution = Solution(**solution_data)
            db.session.add(solution)
        
        causes = [
            {'damage_id': 1, 'description': 'Umur pakai drive belt sudah terlalu lama.'},
            {'damage_id': 4, 'description': 'Drive belt sudah aus parah sehingga menjadi putus.'},
            {'damage_id': 5, 'description': 'Kebocoran oli transmisi atau kebocoran oli dari bagian mesin.'}
        ]
        
        for cause_data in causes:
            cause = Cause(**cause_data)
            db.session.add(cause)
        
        db.session.commit()
        
        return jsonify({'message': 'Database seeded successfully'}), 200

    @app.route('/')
    def index():
        return jsonify({
            'message': 'Automatic Motorcycle Damage Expert System API',
            'version': '1.0.0'
        })