from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allows requests from any origin (you can restrict to your frontend domain)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()

    # Expecting JSON with a "message" field
    user_message = data.get('message')
    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    # For now, just echo the message back
    response = {
        'reply': f"You said: {user_message}"
    }

    return jsonify(response), 200

@app.route('/iterate', methods=['POST'])
def iterate():
    data = request.get_json()
    iteration_type = data.get('type')

    if iteration_type == 'idea':
        reply = "Here's a new idea to consider."
    elif iteration_type == 'refine':
        reply = "Let's refine the previous idea further."
    elif iteration_type == 'example':
        reply = "Here’s an example to illustrate the concept."
    else:
        reply = f"Unknown iteration type: {iteration_type}"

    return jsonify({'reply': reply}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
