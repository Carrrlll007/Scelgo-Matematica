import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from google import genai 
from google.genai.errors import APIError

# --- FLASK SETUP ---
app = Flask(__name__)
CORS(app)

# --- 🔐 GEMINI SETUP (Versione CORRETTA) ---

# Definisce il NOME standard della variabile d'ambiente.
ENV_VAR_NAME = "GOOGLE_API_KEY" 

# Il codice cerca una variabile d'ambiente di nome "GOOGLE_API_KEY"
API_KEY = os.environ.get(ENV_VAR_NAME) 

# Nome del modello da usare
MODEL_ID = 'gemini-2.5-flash' 

client = None

if API_KEY:
    try:
        # Inizializza il client solo se la chiave è presente
        client = genai.Client(api_key=API_KEY)
        print("INFO: Gemini Client initialized successfully.")
    except Exception as e:
        print(f"ATTENZIONE: Errore durante l'inizializzazione del client Gemini: {e}")
        client = None
else:
    # Il messaggio di warning ora usa il nome corretto della variabile
    print(f"WARNING: Variabile d'ambiente {ENV_VAR_NAME} non trovata. Le funzionalità AI non funzioneranno.")


# --- HELPER FUNCTION FOR AI MODES (Goal 3) ---
def get_mode_prompt(mode_name):
    """Maps the user-selected mode to a specific tutor persona."""
    
    # Base instruction to avoid boxed answers
    no_box_instruction = " Do not use the \\boxed{} command or any boxing for the final answer. Just write the answer plainly."

    if mode_name == 'explain_like_im_10':
        return "You are a fun, enthusiastic tutor. Explain the math problem using simple words and relatable analogies, as if speaking to a 10-year-old. Use emojis and keep the tone light. Ensure all math is clear." + no_box_instruction
    elif mode_name == 'walk_me_slowly':
        return "You are a very methodical and patient teacher. Break the solution into the smallest, most digestible steps (no more than one operation per line), explaining the *why* after every line of computation. Use Markdown for clarity." + no_box_instruction
    elif mode_name == 'strict_examiner':
        return "You are a formal, strict university examiner. Provide the solution using only mathematically rigorous notation, giving a clean, concise derivation and final answer. Do not use conversational language or excessive explanation." + no_box_instruction
    else: # Default: 'teacher_mode'
        return "You are a professional math tutor. Provide a clear, detailed, step-by-step solution using standard academic language. Use LaTex for math formulas where appropriate." + no_box_instruction


# --- API ROUTE PER MATH AGENT (Goal 3 Integration) ---
@app.route("/api/solve", methods=["POST"])
def solve():
    data = request.get_json(force=True)
    problem = data.get("problem", "").strip()
    selected_mode = data.get("mode", "teacher_mode")

    if not problem:
        return jsonify({"solution": "Nessun problema fornito."}), 400
    
    # Controlla se il client è stato inizializzato.
    if not client:
        return jsonify({"solution": "Il Math Agent non è attivo. L'API key non è configurata correttamente sul server."}), 503

    system_instruction = get_mode_prompt(selected_mode)

    try:
        # Usiamo MODEL_ID nella chiamata al client
        response = client.models.generate_content(
            model=MODEL_ID, # Passiamo la stringa del nome del modello
            contents=problem,
            config={
                "system_instruction": system_instruction,
                "temperature": 0.3
            }
        )
        return jsonify({"solution": response.text})
    
    except APIError as e:
        return jsonify({"solution": f"Errore API del Math Agent. Controlla la chiave e il modello. Dettagli: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"solution": f"Si è verificato un errore inatteso sul server: {str(e)}"}), 500

# --- API ROUTE PER ADAPTIVE LEARNING (Goal 1) ---
@app.route('/api/analyze_mistake', methods=['POST'])
def analyze_mistake():
    # Controlliamo se il client è stato inizializzato
    if not client:
        return jsonify({"analysis": "Il Math Agent non è attivo."}), 503
        
    data = request.json
    if data is None:
        return jsonify({'error': "Richiesta non valida: corpo JSON mancante o malformato.", 'status': 'error'}), 400
    problem = data.get('problem')
    student_answer = data.get('student_answer')

    analysis_prompt = (
        f"The student attempted to solve the problem: '{problem}'. The student's answer was: '{student_answer}'. "
        f"First, provide a detailed analysis of the likely conceptual mistake the student made (e.g., failed to distribute, error in sign change, exponent rule violation). "
        f"Second, generate a new, similar math problem (without the solution) that specifically focuses on testing and fixing that identified weakness."
        f"Structure your entire response as a clean JSON object with two keys: 'mistake_analysis' (string) and 'new_problem' (string). Use LaTex for the math in the new problem."
    )

    try:
        response = client.models.generate_content(
            model=MODEL_ID, # Usiamo la stringa del nome del modello
            contents=analysis_prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "object",
                    "properties": {
                        "mistake_analysis": {"type": "string"},
                        "new_problem": {"type": "string"},
                    },
                    "required": ["mistake_analysis", "new_problem"],
                },
            }
        )
        return jsonify({"analysis_data": response.text, 'status': 'success'})
    except Exception as e:
        error_message = str(e)
        if "JSON" in error_message:
            return jsonify({'error': "Gemini non ha restituito JSON pulito. Riprova.", 'status': 'error'}), 500
        return jsonify({'error': f"Errore nell'analisi: {error_message}", 'status': 'error'}), 500


# --- Basic HTML Routes (Adjust if you use Flask Templating) ---
@app.route('/')
def index_route():
    # Per ora, solo un placeholder se hai bisogno di un route funzionante:
    return "MathHub Server Running. Access index.html directly if running locally."

if __name__ == "__main__":
    app.run(debug=True)