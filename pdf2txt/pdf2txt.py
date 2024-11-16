from flask import Flask, request, jsonify
import pdfplumber
import os
from google.cloud import storage
import config

app = Flask(__name__)

def get_output_path(input_path):
    """
    Convierte la ruta de entrada en la ruta de salida correspondiente
    Ejemplo:
    Entrada: uuid/Falabella/Step1_Unlocked/archivo.pdf
    Salida:  uuid/Falabella/Step2_pdf2txt/archivo.txt
    """
    # Obtener el nombre base del archivo sin extensión
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    
    # Reemplazar Step1_Unlocked por Step2_pdf2txt en la ruta
    if 'Step1_Unlocked' in input_path:
        parent_path = os.path.dirname(input_path)
        new_parent_path = parent_path.replace('Step1_Unlocked', 'Step2_pdf2txt')
        return f"{new_parent_path}/{base_name}.txt"
    
    # Si por alguna razón no encuentra Step1_Unlocked, construir la ruta usando el nombre del archivo
    parent_dir = os.path.dirname(input_path)
    base_dir = parent_dir.split('/Falabella/')[0]
    return f"{base_dir}/Falabella/Step2_pdf2txt/{base_name}.txt"

def extract_text_from_pdf(input_file_path):
    """
    Extrae el texto de un archivo PDF
    """
    try:
        with pdfplumber.open(input_file_path) as pdf:
            text = ''
            for page in pdf.pages:
                extracted_text = page.extract_text()
                if extracted_text:
                    text += extracted_text + '\n'
            return text
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
        raise

def save_text_to_file(text, output_path):
    """
    Guarda el texto extraído en un archivo en Google Cloud Storage
    """
    try:
        storage_client = storage.Client()
        bucket = storage_client.bucket(config.GCS_BUCKET_NAME)
        blob = bucket.blob(output_path)
        
        # Guardar temporalmente el archivo de texto
        with open(config.TEMP_TXT_PATH, 'w', encoding='utf-8') as file:
            file.write(text)
        
        # Subir el archivo al bucket
        blob.upload_from_filename(config.TEMP_TXT_PATH)
        
        # Limpiar archivo temporal
        os.remove(config.TEMP_TXT_PATH)
        
    except Exception as e:
        print(f"Error saving text to file: {str(e)}")
        raise

@app.route('/pdf2txt', methods=['POST'])
def pdf2txt_route():
    try:
        data = request.json
        input_file_path = data.get('input_file_path')

        if not input_file_path:
            return jsonify({'error': 'Missing input_file_path'}), 400

        # Generar la ruta de salida basada en la ruta de entrada
        output_file_path = get_output_path(input_file_path)

        # Descargar el archivo PDF desde Google Cloud Storage
        storage_client = storage.Client()
        bucket = storage_client.bucket(config.GCS_BUCKET_NAME)
        input_blob = bucket.blob(input_file_path)
        
        input_blob.download_to_filename(config.TEMP_PDF_PATH)

        # Extraer el texto del PDF
        text = extract_text_from_pdf(config.TEMP_PDF_PATH)
        
        # Guardar el texto extraído
        save_text_to_file(text, output_file_path)

        # Limpiar archivo temporal
        os.remove(config.TEMP_PDF_PATH)

        return jsonify({
            'message': 'PDF convertido exitosamente',
            'output_txt_path': output_file_path
        }), 200

    except Exception as e:
        print(f"Error in pdf2txt conversion: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT)