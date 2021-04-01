# Python standard libraries
import json
import os
import sqlite3

# Third-party libraries
from flask import Flask, redirect, request, url_for, jsonify
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests

from db import init_db_command
from user import User

# Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Inicializa o banco de dados
try:
    init_db_command()
except sqlite3.OperationalError:
    # Assume que ele ja foi criado
    pass

# Funcao ajuda carregar informacoes de usuarios do banco de dados
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Endpoints
# Homepage:       /
# Login:          /login
# Login Callback: /login/callback
# Logout:         /logout

# HOMEPAGE
#
# Isso não é nada sofisticado visualmente, mas você adicionará uma lógica
# interessante para exibir algo diferente se um usuário estiver conectado.
# Quando ele não estiver conectado, aparecerá um link que diz Login do Google.
# Pressionar o link os redirecionará para seu endpoint "/login", que iniciará o
# fluxo de login. Após um login bem-sucedido, a página inicial agora exibirá o
# e-mail do usuário do Google e sua foto pública do perfil do Google!
@app.route("/")
def index():
    if current_user.is_authenticated:
        response_data = {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "profile_picture": current_user.profile_pic
        }
        return jsonify(response_data)
    else:
        return '<a class="button" href="/login">Google Login</a>'

# LOGIN 

# Função rápida e ingênua para recuperar a configuração do provedor do Google
def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

# O campo do documento de configuração do provedor de que você precisa é chamado
# de authorization_endpoint. Ele conterá o URL que você precisa usar para
# iniciar o fluxo OAuth 2 com o Google a partir de seu aplicativo cliente.
@app.route("/login")
def login():
    # Descubra qual URL deve ser acessado para fazer login no Google
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Usa a biblioteca para construir a solicitação de login do Google e
    # fornecer escopos que permitem recuperar o perfil do usuário do Google
    request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=request.base_url + "/callback",
            scope=["openid", "email", "profile"]
    )
    return redirect(request_uri)

# LOGIN CALLBACK
#
# Quando o Google enviar de volta esse código exclusivo, ele o enviará a este
# ponto de extremidade de retorno de chamada de login em seu aplicativo.
# Portanto, sua primeira etapa é definir o endpoint e obter esse código.
@app.route("/login/callback")
def callback():
    # Pegar o código de autenticação que o Google enviou para esse endpoint
    code = request.args.get("code")

    # Descubra qual URL atingir para obter tokens que permitem que você pergunte
    # coisas em nome de um usuário
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    
    # Preparar a requisição pra receber os tokens
    token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url,
            redirect_url=request.base_url,
            code=code
    )

    # Faz a requisição POST pra receber os tokens do Google
    token_response = requests.post(token_url, headers=headers, data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET))

    # Parse tokens
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Agora que temos os tokens, podemos fazer uma requisição ao endpoint do
    # Google que fornece as informações básicas de usuário: userinfo_endpoint.
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    unique_id = userinfo_response.json()["sub"]
    user_email = userinfo_response.json()["email"]
    user_name = userinfo_response.json()["given_name"]
    picture = userinfo_response.json()["picture"]

    # Cria novo usuário no app com as informações de usuário obtidas do Google
    user = User(unique_id, user_name, user_email, picture)
    if not User.get(unique_id):
        User.create(unique_id, user_name, user_email, picture)

    # Iniciliza sessão de usuário
    login_user(user)

    # Redireciona o usuario para a homepage
    return redirect(url_for("index"))


# LOGOUT

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

# Pra usar o OAuth2 é preciso estar se comunicando sobre o HTTPS e não HTTP
# Pra deixar isso padrão, o aplicativo é executado com certificado "adhoc".
#if __name__ == "__main__":
#    app.run(ssl_context='adhoc')

