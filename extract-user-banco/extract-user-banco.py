from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/extractUsuarioAndBanco', methods=['POST'])
def extract_usuario_banco():
    data = request.json  # Recibe el JSON con el objectId
    objectId = data.get('objectId')
    
    if not objectId:
        return jsonify({"result": "Error", "message": "objectId is required"}), 400

    if "Step0" not in objectId:
        return jsonify({"result": "Error", "message": "Unsupported folder. Only files in 'Step0' are processed."}), 200

    # Extrae el usuario y el banco
    try:
        usuario_end = objectId.index("/")
        usuario = objectId[:usuario_end]
        banco_start = usuario_end + 1
        banco_end = objectId.index("/", banco_start)
        banco = objectId[banco_start:banco_end]
        
        return jsonify({
            "result": "Success",
            "usuario": usuario,
            "banco": banco
        })
    
    except ValueError:
        return jsonify({"result": "Error", "message": "Invalid objectId format"}), 400

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
