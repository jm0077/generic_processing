from google.cloud import storage
import PyPDF2
import os
from flask import Flask, request, jsonify
import config
import re

app = Flask(__name__)

@app.route('/unlock', methods=['POST'])
def unlock():
    data = request.json
    input_file_path = data.get('input_file_path')
    password = data.get('password')
    
    if not input_file_path or not password:
        return jsonify({"error": "input_file_path and password are required"}), 400
    
    output_pdf_path = process_pdf(input_file_path, password)
    
    if output_pdf_path:
        return jsonify({
            "message": "PDF procesado con éxito", 
            "output_pdf_path": output_pdf_path
        })
    else:
        return jsonify({"error": "Error al procesar el PDF"}), 400

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
        bucket = storage_client.bucket(config.GCS_BUCKET_NAME)
        
        # Descargar el archivo PDF del bucket
        input_blob = bucket.blob(input_file_path)
        input_blob.download_to_filename(config.TEMP_DOWNLOAD_PATH)
        
        with open(config.TEMP_DOWNLOAD_PATH, 'rb') as input_file:
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
            with open(config.TEMP_UNLOCKED_PATH, 'wb') as output_file:
                pdf_writer.write(output_file)
            
            # Subir el archivo procesado al bucket
            output_blob = bucket.blob(output_blob_path)
            output_blob.upload_from_filename(config.TEMP_UNLOCKED_PATH)
            
            # Limpiar archivos temporales
            os.remove(config.TEMP_DOWNLOAD_PATH)
            os.remove(config.TEMP_UNLOCKED_PATH)
            
            return output_blob_path
            
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        return None

if __name__ == '__main__':
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT)