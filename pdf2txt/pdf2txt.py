from flask import Flask, request, jsonify
import pdfplumber
import os
from google.cloud import storage

app = Flask(__name__)

def extract_text_from_pdf(input_file_path):
    with pdfplumber.open(input_file_path) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text() + '\n'
        return text

def save_text_to_file(text, output_path):
    storage_client = storage.Client()
    bucket_name = 'custom-curve-431820-e9_cloudbuild'
    blob = storage_client.bucket(bucket_name).blob(output_path)
    
    with open('/tmp/temp.txt', 'w', encoding='utf-8') as file:
        file.write(text)
    
    with open('/tmp/temp.txt', 'rb') as file:
        blob.upload_from_file(file)

@app.route('/pdf2txt', methods=['POST'])
def pdf2txt_route():
    data = request.json
    input_file_path = data.get('input_file_path')

    if not input_file_path:
        return jsonify({'error': 'Missing input_file_path'}), 400

    # Definir el subdirectorio de salida
    output_folder = 'Falabella/Step2_pdf2txt'
    
    # Generar la ruta completa para el archivo de salida en el bucket
    base_name, ext = os.path.splitext(os.path.basename(input_file_path))
    output_file = os.path.join(output_folder, f"{base_name}_converted.txt")

    # Descarga del archivo PDF desde Google Cloud Storage
    storage_client = storage.Client()
    bucket_name = 'custom-curve-431820-e9_cloudbuild'
    blob = storage_client.bucket(bucket_name).blob(input_file_path)
    
    with open('/tmp/temp.pdf', 'wb') as file:
        blob.download_to_file(file)

    # Extraer y guardar el texto del archivo PDF
    text = extract_text_from_pdf('/tmp/temp.pdf')
    save_text_to_file(text, output_file)

    return jsonify({'output_txt_path': output_file}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
