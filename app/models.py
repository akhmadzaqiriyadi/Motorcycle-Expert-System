from . import db
from datetime import datetime

class Motorcycle(db.Model):
    __tablename__ = 'motorcycles'
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'brand': self.brand,
            'model': self.model
        }

class Damage(db.Model):
    __tablename__ = 'damages'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    causes = db.relationship('Cause', backref='damage', lazy=True)
    solutions = db.relationship('Solution', backref='damage', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description,
            'causes': [cause.to_dict() for cause in self.causes],
            'solutions': [solution.to_dict() for solution in self.solutions]
        }

class Symptom(db.Model):
    __tablename__ = 'symptoms'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'code': self.code,
            'name': self.name,
            'description': self.description
        }

class Cause(db.Model):
    __tablename__ = 'causes'
    id = db.Column(db.Integer, primary_key=True)
    damage_id = db.Column(db.Integer, db.ForeignKey('damages.id'), nullable=False)
    description = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'damage_id': self.damage_id,
            'description': self.description
        }

class Solution(db.Model):
    __tablename__ = 'solutions'
    id = db.Column(db.Integer, primary_key=True)
    damage_id = db.Column(db.Integer, db.ForeignKey('damages.id'), nullable=False)
    description = db.Column(db.Text)
    
    def to_dict(self):
        return {
            'id': self.id,
            'damage_id': self.damage_id,
            'description': self.description
        }

class Rule(db.Model):
    __tablename__ = 'rules'
    id = db.Column(db.Integer, primary_key=True)
    damage_id = db.Column(db.Integer, db.ForeignKey('damages.id'), nullable=False)
    symptoms = db.relationship('RuleSymptom', backref='rule', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'damage_id': self.damage_id,
            'symptoms': [rule_symptom.symptom_id for rule_symptom in self.symptoms]
        }

class RuleSymptom(db.Model):
    __tablename__ = 'rule_symptoms'
    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey('rules.id'), nullable=False)
    symptom_id = db.Column(db.Integer, db.ForeignKey('symptoms.id'), nullable=False)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class Consultation(db.Model):
    __tablename__ = 'consultations'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    motorcycle_id = db.Column(db.Integer, db.ForeignKey('motorcycles.id'), nullable=False)
    damage_id = db.Column(db.Integer, db.ForeignKey('damages.id'))
    consultation_date = db.Column(db.DateTime, default=datetime.utcnow)
    symptoms = db.relationship('ConsultationSymptom', backref='consultation', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'motorcycle_id': self.motorcycle_id,
            'damage_id': self.damage_id,
            'consultation_date': self.consultation_date.strftime('%Y-%m-%d %H:%M:%S'),
            'symptoms': [cs.symptom_id for cs in self.symptoms]
        }

class ConsultationSymptom(db.Model):
    __tablename__ = 'consultation_symptoms'
    id = db.Column(db.Integer, primary_key=True)
    consultation_id = db.Column(db.Integer, db.ForeignKey('consultations.id'), nullable=False)
    symptom_id = db.Column(db.Integer, db.ForeignKey('symptoms.id'), nullable=False)