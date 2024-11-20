from google.cloud import storage
import PyPDF2
import os
from flask import Flask, request, jsonify
import config
import re
from keycloak import KeycloakAdmin
import requests
import logging
import json

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def get_keycloak_admin_token():
    """Obtener token de administrador de Keycloak"""
    data = {
        'grant_type': 'client_credentials',
        'client_id': config.Config.KEYCLOAK_CLIENT_ID,
        'client_secret': config.Config.KEYCLOAK_CLIENT_SECRET
    }
    
    try:
        logger.debug("Attempting to get Keycloak admin token")
        response = requests.post(
            f"{config.Config.KEYCLOAK_SERVER_URL}/realms/{config.Config.KEYCLOAK_REALM_NAME}/protocol/openid-connect/token", 
            data=data
        )
        
        logger.debug(f"Token response status: {response.status_code}")
        logger.debug(f"Token response: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            return token_data.get('access_token')
        else:
            logger.error(f"Failed to get Keycloak admin token: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error obtaining Keycloak admin token: {str(e)}")
        return None

def get_user_dni(user_id):
    """Obtener el DNI del usuario desde Keycloak"""
    try:
        token = get_keycloak_admin_token()
        
        if not token:
            logger.error("Could not obtain Keycloak admin token")
            return None
        
        logger.debug(f"Attempting to get user info for user_id: {user_id}")
        
        # Crear la URL para obtener la información del usuario
        user_url = f"{config.Config.KEYCLOAK_SERVER_URL}/admin/realms/{config.Config.KEYCLOAK_REALM_NAME}/users/{user_id}"
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(user_url, headers=headers)
        logger.debug(f"User info response status: {response.status_code}")
        logger.debug(f"User info response: {response.text}")
        
        if response.status_code == 200:
            user_info = response.json()
            dni = user_info.get('attributes', {}).get('dni', [None])[0]
            
            if dni:
                logger.debug(f"DNI found for user {user_id}")
                return dni
            else:
                logger.error(f"No DNI found for user {user_id}")
                return None
        else:
            logger.error(f"Failed to get user info: {response.text}")
            return None
    
    except Exception as e:
        logger.error(f"Error retrieving user DNI: {str(e)}")
        return None

@app.route('/unlock', methods=['POST'])
def unlock():
    data = request.json
    input_file_path = data.get('input_file_path')
    
    if not input_file_path:
        return jsonify({"error": "input_file_path is required"}), 400
    
    try:
        # Extraer el user ID de la ruta del archivo
        match = re.match(r'^([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})', input_file_path)
        if not match:
            return jsonify({"error": "Invalid file path format. Cannot extract user ID"}), 400
        
        user_id = match.group(1)
        logger.debug(f"Extracted user_id: {user_id}")
        
        # Obtener el DNI desde Keycloak
        password = get_user_dni(user_id)
        
        if not password:
            return jsonify({"error": "No se pudo obtener la contraseña del usuario"}), 400
        
        output_pdf_path = process_pdf(input_file_path, password)
        
        if output_pdf_path:
            return jsonify({
                "message": "PDF procesado con éxito", 
                "output_pdf_path": output_pdf_path
            })
        else:
            return jsonify({"error": "Error al procesar el PDF"}), 400
            
    except Exception as e:
        logger.error(f"Error in unlock endpoint: {str(e)}")
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500

def get_output_path(input_path):
    """
    Convierte la ruta de entrada en la ruta de salida correspondiente
    Ejemplo:
    Entrada: uuid/Falabella/Step0_Input/archivo.pdf
    Salida:  uuid/Falabella/Step1_Unlocked/archivo.pdf
    """
    # Reemplazar Step0_Input por Step1_Unlocked en la ruta
    if 'Step0_Input' in input_path:
        return input_path.replace('Step0_Input', 'Step1_Unlocked')
    
    # Si por alguna razón no encuentra Step0_Input, construir la ruta usando el nombre del archivo
    filename = os.path.basename(input_path)
    parent_dir = os.path.dirname(input_path)
    base_dir = parent_dir.split('/Falabella/')[0]
    return f"{base_dir}/Falabella/Step1_Unlocked/{filename}"

def process_pdf(input_file_path, password):
    try:
        # Obtener la ruta de salida basada en la ruta de entrada
        output_blob_path = get_output_path(input_file_path)
        
        storage_client = storage.Client()
        bucket = storage_client.bucket(config.Config.GCS_BUCKET_NAME)
        
        # Descargar el archivo PDF del bucket
        input_blob = bucket.blob(input_file_path)
        input_blob.download_to_filename(config.Config.TEMP_DOWNLOAD_PATH)
        
        with open(config.Config.TEMP_DOWNLOAD_PATH, 'rb') as input_file:
            pdf_reader = PyPDF2.PdfReader(input_file)
            pdf_writer = PyPDF2.PdfWriter()
            
            # Si el PDF está encriptado, intentar desencriptarlo
            if pdf_reader.is_encrypted:
                try:
                    pdf_reader.decrypt(password)
                except:
                    raise Exception("Error al desencriptar el PDF: contraseña incorrecta")
            
            # Copiar todas las páginas al nuevo PDF
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                pdf_writer.add_page(page)
            
            # Guardar el PDF procesado
            with open(config.Config.TEMP_UNLOCKED_PATH, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            # Subir el archivo procesado al bucket
            output_blob = bucket.blob(output_blob_path)
            output_blob.upload_from_filename(config.Config.TEMP_UNLOCKED_PATH)
            
            # Limpiar archivos temporales
            os.remove(config.Config.TEMP_DOWNLOAD_PATH)
            os.remove(config.Config.TEMP_UNLOCKED_PATH)
            
            return output_blob_path
            
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}")
        return None

if __name__ == '__main__':
    app.run(host=config.Config.FLASK_HOST, port=config.Config.FLASK_PORT)