# Main Flask web server
import os
from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename

# Import your core functions from the src package
from src.pattern_recognition.tile_recognition import tile_recognition
from src.pattern_recognition.main import check_win_condition

# --- Flask App Configuration ---
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Web Page Routes ---

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(image_path)

            # --- Call Your Backend Logic ---
            print(f"Recognizing tiles in {image_path}")
            bing, bamboo, wan, words, bonus = tile_recognition(image_path)

            print("Checking win condition...")
            # You might need to pass the 'others' dictionary here if your function requires it
            final_money, final_breakdown = check_win_condition(bing, bamboo, wan, words, bonus)
            
            # --- Render the Results Page ---
            return render_template('result.html', 
                                   money=final_money, 
                                   breakdown=final_breakdown, 
                                   image_file=filename)

    # For a GET request, just show the upload form
    return render_template('index.html')

if __name__ == '__main__':
    # Create the upload folder if it doesn't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True) # debug=True is for development only