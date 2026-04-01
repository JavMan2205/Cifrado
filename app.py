from flask import Flask, request, jsonify
from models import db, RegistroCifrado
from crypto_utils import CryptoManager, generar_token_unico
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app_segura.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
crypto = CryptoManager()

@app.route('/crear', methods=['POST'])
def crear_registro():
    data = request.json
    usuario = data.get('usuario')
    texto = data.get('texto')
    
    if not texto or not usuario:
        return jsonify({"error": "Faltan datos"}), 400

    token = generar_token_unico()
    cifrado = crypto.cifrar_texto(texto)
    
    nuevo = RegistroCifrado(
        usuario_creador=usuario,
        texto_binario=cifrado,
        token=token,
        fecha_expiracion=datetime.utcnow() + timedelta(days=7)
    )
    
    db.session.add(nuevo)
    db.session.commit()
    return jsonify({"mensaje": "Éxito", "token": token})

@app.route('/leer/<token>', methods=['GET'])
def leer_registro(token):
    registro = RegistroCifrado.query.filter_by(token=token).with_for_update().first()
    
    if not registro or registro.estado != 'ACTIVO' or registro.fecha_expiracion < datetime.utcnow():
        return jsonify({"error": "Token Inválido"}), 403

    texto_plano = crypto.descifrar_texto(registro.texto_binario)
    
    registro.estado = 'LEIDO'
    registro.fecha_lectura = datetime.utcnow()
    registro.ip_acceso = request.remote_addr
    registro.user_agent = str(request.user_agent)
    
    db.session.commit()
    return jsonify({"texto": texto_plano, "autor": registro.usuario_creador})

@app.route('/historial/<usuario>', methods=['GET'])
def ver_historial(usuario):
    registros = RegistroCifrado.query.filter_by(usuario_creador=usuario).all()
    historial = []
    for r in registros:
        historial.append({
            "token": r.token,
            "estado": r.estado,
            "creado": r.fecha_creacion.strftime("%Y-%m-%d %H:%M:%S"),
            "leido_el": r.fecha_lectura.strftime("%Y-%m-%d %H:%M:%S") if r.fecha_lectura else "Pendiente"
        })
    return jsonify(historial)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(port=5000)