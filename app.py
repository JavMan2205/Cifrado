from flask import Flask, request, jsonify, render_template_string
from models import db, RegistroCifrado
from crypto_utils import CryptoManager, generar_token_unico
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app_segura.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
crypto = CryptoManager()

CSS = """
<style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background-color: #f0f2f5; color: #333; }
    .container { max-width: 800px; margin: auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
    h1 { color: #1a73e8; border-bottom: 2px solid #e8eaed; padding-bottom: 10px; }
    .btn { background: #1a73e8; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; text-decoration: none; display: inline-block; }
    .btn-red { background: #d93025; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { text-align: left; padding: 12px; border-bottom: 1px solid #ddd; }
    tr:hover { background-color: #f8f9fa; }
    .status-active { color: #1e8e3e; font-weight: bold; }
    .status-read { color: #70757a; }
    textarea { width: 100%; height: 100px; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; }
</style>
"""

@app.route('/')
def index():
    return render_template_string(f"""
    {CSS}
    <div class="container">
        <h1>🔐 Caja Fuerte Digital (RSA-2048)</h1>
        <p>Bienvenido <b>Ingeniero</b>. Use esta app para proteger información sensible.</p>
        
        <div style="background: #e8f0fe; padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3>Cifrar Nuevo Mensaje</h3>
            <form action="/crear_web" method="POST">
                <input type="text" name="usuario" value="Ingeniero" readonly style="padding:8px; background:#ddd;"><br>
                <textarea name="texto" placeholder="Escribe el mensaje secreto aquí..." required></textarea><br>
                <button type="submit" class="btn">Generar Token Seguro</button>
            </form>
        </div>
        
        <a href="/historial_visual/Ingeniero" class="btn" style="background:#5f6368;">Ver Auditoría de Mensajes</a>
    </div>
    """)

@app.route('/crear_web', methods=['POST'])
def crear_web():
    usuario = request.form.get('usuario')
    texto = request.form.get('texto')
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
    
    return render_template_string(f"""
    {CSS}
    <div class="container" style="text-align:center;">
        <h1>✅ Mensaje Cifrado</h1>
        <p>Comparte este token con el destinatario. <b>Solo podrá usarse una vez.</b></p>
        <div style="font-size: 24px; background: #f8f9fa; border: 2px dashed #1a73e8; padding: 20px; margin: 20px 0; font-family: monospace;">
            {token}
        </div>
        <a href="/" class="btn">Volver al Inicio</a>
    </div>
    """)

@app.route('/historial_visual/<usuario>')
def historial_visual(usuario):
    registros = RegistroCifrado.query.filter_by(usuario_creador=usuario).order_by(RegistroCifrado.fecha_creacion.desc()).all()
    filas = ""
    for r in registros:
        estado_html = f'<span class="status-active">Disponible</span>' if r.estado == 'ACTIVO' else f'<span class="status-read">Leído</span>'
        filas += f"""
        <tr>
            <td><code>{r.token}</code></td>
            <td>{estado_html}</td>
            <td>{r.fecha_creacion.strftime('%H:%M:%S - %d/%m/%y')}</td>
            <td>{r.ip_acceso if r.ip_acceso else '-'}</td>
            <td><small>{r.user_agent[:30] if r.user_agent else '-'}</small></td>
        </tr>
        """
    
    return render_template_string(f"""
    {CSS}
    <div class="container">
        <h1>📋 Registro de Auditoría</h1>
        <p>Usuario: <b>{usuario}</b></p>
        <table>
            <thead>
                <tr>
                    <th>Token</th>
                    <th>Estado</th>
                    <th>Creado</th>
                    <th>IP Acceso</th>
                    <th>Dispositivo</th>
                </tr>
            </thead>
            <tbody>{filas}</tbody>
        </table>
        <br><a href="/" class="btn">Volver</a>
    </div>
    """)

@app.route('/leer/<token>')
def leer_visual(token):
    registro = RegistroCifrado.query.filter_by(token=token).with_for_update().first()
    
    if not registro or registro.estado != 'ACTIVO':
        return render_template_string(f"{CSS}<div class='container' style='text-align:center;'><h1>❌ Error</h1><p>El token es inválido o ya fue utilizado.</p><a href='/' class='btn'>Volver</a></div>"), 403

    texto_plano = crypto.descifrar_texto(registro.texto_binario)
    
    registro.estado = 'LEIDO'
    registro.fecha_lectura = datetime.utcnow()
    registro.ip_acceso = request.remote_addr
    registro.user_agent = str(request.user_agent)
    db.session.commit()

    return render_template_string(f"""
    {CSS}
    <div class="container" style="border-top: 5px solid #d93025;">
        <h1>🔓 Mensaje Descifrado</h1>
        <p style="color:red;"><b>AVISO:</b> Este mensaje se ha eliminado de la base de datos y no puede volver a consultarse.</p>
        <div style="background: #fff3e0; padding: 20px; border-left: 5px solid #ff9800; font-size: 18px; margin: 20px 0;">
            {texto_plano}
        </div>
        <p><small>Autor: {registro.usuario_creador} | Leído el: {registro.fecha_lectura.strftime('%H:%M:%S')}</small></p>
        <a href="/" class="btn">Cerrar</a>
    </div>
    """)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)