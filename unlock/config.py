import os
import json
import logging

# Configuración de logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Cargar el archivo client_secrets.json
try:
    with open('client_secrets.json') as f:
        client_secrets = json.load(f)
except FileNotFoundError:
    logger.error("client_secrets.json no encontrado")
    client_secrets = {
        "web": {
            "client_id": os.environ.get('KEYCLOAK_CLIENT_ID'),
            "client_secret": os.environ.get('KEYCLOAK_CLIENT_SECRET'),
            "issuer": os.environ.get('KEYCLOAK_ISSUER'),
            "token_uri": os.environ.get('KEYCLOAK_TOKEN_URI')
        }
    }

class Config:
    # Flask Configuration
    FLASK_HOST = '0.0.0.0'
    FLASK_PORT = 8080
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'you-will-never-guess')

    # Temporary file paths
    TEMP_DOWNLOAD_PATH = '/tmp/temp.pdf'
    TEMP_UNLOCKED_PATH = '/tmp/unlocked.pdf'

    # Google Cloud Storage Configuration
    GCS_BUCKET_NAME = 'account-statements_customers'

    # Keycloak Configuration
    KEYCLOAK_SERVER_URL = client_secrets['web']['issuer'].rstrip('/realms/master')
    KEYCLOAK_REALM_NAME = 'master'
    KEYCLOAK_CLIENT_ID = client_secrets['web']['client_id']
    KEYCLOAK_CLIENT_SECRET = client_secrets['web']['client_secret']
    KEYCLOAK_TOKEN_URI = client_secrets['web']['token_uri']

    # Logging de configuración
    logger.debug(f"KEYCLOAK_SERVER_URL: {KEYCLOAK_SERVER_URL}")
    logger.debug(f"KEYCLOAK_REALM_NAME: {KEYCLOAK_REALM_NAME}")
    logger.debug(f"KEYCLOAK_CLIENT_ID: {KEYCLOAK_CLIENT_ID}")
    logger.debug(f"KEYCLOAK_TOKEN_URI: {KEYCLOAK_TOKEN_URI}")
    logger.debug(f"GCS_BUCKET_NAME: {GCS_BUCKET_NAME}")