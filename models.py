from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class RegistroCifrado(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_creador = db.Column(db.String(80), nullable=False)
    texto_binario = db.Column(db.LargeBinary, nullable=False)
    token = db.Column(db.String(20), unique=True, nullable=False)
    
    estado = db.Column(db.String(20), default='ACTIVO')
    
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_lectura = db.Column(db.DateTime)
    fecha_expiracion = db.Column(db.DateTime)
    ip_acceso = db.Column(db.String(50))
    user_agent = db.Column(db.Text)