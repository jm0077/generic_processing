from google.cloud import storage
import PyPDF2
import os
from flask import Flask, request, jsonify

app = Flask(__name__)

# Define el folder de salida
output_folder = "Falabella/Step1_Unlocked"

@app.route('/unlock', methods=['POST'])
def unlock():
    data = request.json
    input_file_path = data.get('input_file_path')
    password = data.get('password')
    
    if not input_file_path or not password:
        return jsonify({"error": "input_file_path and password are required"}), 400
    
    output_pdf_path = unblock_pdf(input_file_path, password)
    
    if output_pdf_path:
        return jsonify({"message": "PDF desbloqueado con éxito", "output_pdf_path": output_pdf_path})
    else:
        return jsonify({"error": "No se pudo desbloquear el PDF"}), 400

def unblock_pdf(input_file_path, password):
    base_name, ext = os.path.splitext(os.path.basename(input_file_path))
    output_pdf_name = f"{base_name}_unlocked{ext}"
    
    storage_client = storage.Client()
    bucket_name = 'account-statements_customers'
    
    # Descargar el archivo PDF del bucket
    blob = storage_client.bucket(bucket_name).blob(input_file_path)
    
    with open('/tmp/temp.pdf', 'wb') as file_obj:
        blob.download_to_file(file_obj)
    
    with open('/tmp/temp.pdf', 'rb') as input_file:
        pdf_reader = PyPDF2.PdfReader(input_file)
        if pdf_reader.is_encrypted:
            pdf_reader.decrypt(password)
            pdf_writer = PyPDF2.PdfWriter()
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                pdf_writer.add_page(page)
            with open('/tmp/unlocked.pdf', 'wb') as output_file:
                pdf_writer.write(output_file)
            
            # Subir el archivo desbloqueado al folder de salida fijo
            output_blob_path = os.path.join(output_folder, output_pdf_name)
            blob = storage_client.bucket(bucket_name).blob(output_blob_path)
            blob.upload_from_filename('/tmp/unlocked.pdf')
            return output_blob_path
        else:
            return None

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)