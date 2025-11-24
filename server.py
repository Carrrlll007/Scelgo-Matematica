import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
import os # Import the os module

app = Flask(__name__)
CORS(app)

# 🔐 READ API KEY SECURELY FROM ENVIRONMENT VARIABLE
# Set this variable in your terminal: export GOOGLE_API_KEY="AIzaSy..."
API_KEY = os.environ.get("AIzaSyC0Q2U9W-ftd-K3wYnQvfQF6mnCoY7JKm0")

SYSTEM_PROMPT = """
Sei un tutor di matematica molto bravo.
- Risolvi il problema passo per passo.
- Spiega in modo chiaro a uno studente delle superiori / primo anno università.
- Se non hai abbastanza informazioni, dillo chiaramente.
- Usa notazione matematica leggibile (puoi usare LaTeX inline).
"""

# ... rest of the code is mostly the same ...

@app.route("/api/solve", methods=["POST"])
def solve():
    data = request.get_json(force=True)
    problem = data.get("problem", "").strip()

    if not problem:
        return jsonify({"error": "Nessun problema fornito."}), 400

    if not API_KEY:
        # Check if the environment variable was successfully loaded
        return jsonify({"error": "API key non configurata nelle variabili d'ambiente (GOOGLE_API_KEY non trovata)."}), 500
    
    # ... the rest of the try block remains the same ...

