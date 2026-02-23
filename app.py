# Main Flask web server
import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Import your core functions from the src package
from src.main import backend_main

# --- Flask App Configuration ---
UPLOAD_FOLDER = 'static/uploads'
OUTPUT_FOLDER = 'static/outputs'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
CORS(app) # Enable CORS for all routes
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- API Routes ---

@app.route('/api/analyze', methods=['POST'])
def analyze_hand():
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(image_path)

        # --- Call Your Backend Logic ---
        try:
            others = {
                "round": request.form.get('round', 'east'),
                "dealer": request.form.get('dealer', 'east'),
                "continues": int(request.form.get('continues', 1)),
                "dice": int(request.form.get('dice', 18)),
                "seat": request.form.get('seat', 'east'),
                "wins": request.form.get('wins', 'east'),
                "base": int(request.form.get('base', 100)),
                "bonus": int(request.form.get('bonus', 30)),
            }
            final_money, final_breakdown = backend_main(others)
            
            # The backend_main function likely saves the output image to static/outputs/output.png
            # We'll return the URLs to the images
            
            return jsonify({
                "money": final_money,
                "breakdown": final_breakdown,
                "uploaded_image_url": f"/static/uploads/{filename}",
                "generated_image_url": "/static/outputs/output.png"
            })
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Invalid file type"}), 400

# Serve static files
@app.route('/static/<path:folder>/<path:filename>')
def serve_static(folder, filename):
    if folder == 'uploads':
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    elif folder == 'outputs':
        return send_from_directory(app.config['OUTPUT_FOLDER'], filename)
    return jsonify({"error": "Not found"}), 404

if __name__ == '__main__':
    # Create the folders if they don't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    app.run(debug=True, port=5000) # debug=True is for development only

