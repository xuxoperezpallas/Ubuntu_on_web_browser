import docker
from flask import Flask, render_template, request, redirect
import config
import logging
import time

app = Flask(__name__)
client = docker.from_env()
logging.basicConfig(level=logging.INFO)

@app.route('/')
def index():
    """Página principal con formulario para crear sesiones"""
    return render_template('index.html')

@app.route('/start-session', methods=['POST'])
def start_session():
    """Inicia un nuevo contenedor VNC"""
    username = request.form.get('username', 'invitado')
    
    try:
        # Crear contenedor para el usuario
        container = client.containers.run(
            image=config.VNC_IMAGE,
            name=f"vnc-{username}-{int(time.time())}",
            ports={'80/tcp': None},
            environment={
                'VNC_PASSWORD': request.form.get('password', 'password123'),
                'RESOLUTION': request.form.get('resolution', '1280x720')
            },
            mem_limit=config.RAM_POR_USUARIO,
            detach=True,
            remove=True  # Elimina el contenedor al detenerse
        )
        
        # Obtener puerto asignado
        container.reload()
        port = container.attrs['NetworkSettings']['Ports']['80/tcp'][0]['HostPort']
        
        return render_template('index.html', 
                              session_url=f"http://{config.SERVER_IP}:{port}",
                              username=username)
    
    except Exception as e:
        logging.error(f"Error al iniciar contenedor: {e}")
        return render_template('index.html', error=str(e))

@app.route('/list-sessions')
def list_sessions():
    """Lista las sesiones activas"""
    containers = client.containers.list(
        filters={"ancestor": config.VNC_IMAGE}
    )
    
    sessions = []
    for container in containers:
        port = container.attrs['NetworkSettings']['Ports']['80/tcp'][0]['HostPort']
        sessions.append({
            'id': container.id[:12],
            'name': container.name,
            'port': port,
            'status': container.status,
            'url': f"http://{config.SERVER_IP}:{port}"
        })
    
    return render_template('index.html', sessions=sessions)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=config.MANAGER_PORT)
