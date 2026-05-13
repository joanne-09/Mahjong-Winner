# Imports
import os
import uuid
import random
import string
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit, join_room

from db import db
from src.models import Game, Player, RoundRecord

load_dotenv() # Load environment variables from .env

# Import your core functions from the src package
from src.main import final_backend_main

# --- Flask App Configuration ---
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_ROOT = os.path.abspath(os.getenv('MEDIA_ROOT', os.path.join(BASE_DIR, 'var', 'media')))
UPLOAD_FOLDER = os.path.abspath(os.getenv('UPLOAD_FOLDER', os.path.join(MEDIA_ROOT, 'uploads')))
OUTPUT_FOLDER = os.path.abspath(os.getenv('OUTPUT_FOLDER', os.path.join(MEDIA_ROOT, 'outputs')))
MEDIA_RETENTION_SECONDS = int(os.getenv('MEDIA_RETENTION_SECONDS', '3600'))
MAX_UPLOAD_MB = int(os.getenv('MAX_UPLOAD_MB', '8'))

app = Flask(__name__)
CORS(app) # Enable CORS for all routes
app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_MB * 1024 * 1024

# Database Configuration
# Fallback to local SQLite if DATABASE_URL is not set
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///local_development.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
socketio = SocketIO(app, cors_allowed_origins="*")

with app.app_context():
    # Import models here so they register with SQLAlchemy
    import src.models
    db.create_all()

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER

def ensure_media_dirs():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

def cleanup_old_media_files():
    if MEDIA_RETENTION_SECONDS <= 0:
        return

    expires_before = time.time() - MEDIA_RETENTION_SECONDS
    for folder in (app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER']):
        if not os.path.isdir(folder):
            continue

        for entry in os.scandir(folder):
            if not entry.is_file():
                continue
            try:
                if entry.stat().st_mtime < expires_before:
                    os.remove(entry.path)
            except OSError:
                pass

def media_url(folder, filename):
    return f"/media/{folder}/{filename}"

ensure_media_dirs()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def form_bool(name, default=False):
    value = request.form.get(name)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on", "self", "tsumo"}

def form_int(name, default=0):
    value = request.form.get(name)
    if value is None or value == '':
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

# --- General Helper ---
def generate_room_code(length=6):
    letters_and_digits = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(letters_and_digits, k=length))
        if not Game.query.filter_by(game_code=code).first():
            return code

def get_wind_from_dealer_distance(round_wind, dealer_id, seat_position):
    winds = ['East', 'South', 'West', 'North']
    distance = (seat_position - dealer_id + 4) % 4
    return winds[distance]


# --- API Routes ---
@app.route('/api/game/create', methods=['POST'])
def create_game():
    data = request.json or {}
    players_names = data.get('players', ['Player 1', 'Player 2', 'Player 3', 'Player 4'])
    base_score = data.get('base_score', 0)

    room_code = generate_room_code()
    new_game = Game(game_code=room_code)
    db.session.add(new_game)
    db.session.flush()

    for i, name in enumerate(players_names):
        player = Player(
            game_id=new_game.id,
            name=name,
            money=base_score,
            seat_position=i + 1
        )
        db.session.add(player)

    db.session.commit()
    return jsonify(new_game.to_dict()), 201


@app.route('/api/game/<room_code>', methods=['GET'])
def get_game(room_code):
    game = Game.query.filter_by(game_code=room_code).first()
    if not game:
        return jsonify({"error": "Game not found"}), 404
    return jsonify(game.to_dict())


@app.route('/api/game/<room_code>/win', methods=['POST'])
def process_win(room_code):
    game = Game.query.filter_by(game_code=room_code).first()
    if not game:
        return jsonify({"error": "Game not found"}), 404

    data = request.json
    winner_id = data.get('winner_id')
    points = data.get('points', 0)
    win_type = data.get('win_type', 'ron') # 'tsumo' or 'ron'
    loser_id = data.get('loser_id') # Only for 'ron'

    winner = Player.query.get(winner_id)
    if not winner or winner.game_id != game.id:
        return jsonify({"error": "Invalid winner"}), 400

    is_dealer_win = (winner.seat_position == game.dealer_id)

    # Calculate payouts (simplified for this example - adjust to your real rules)
    payout = points
    if win_type == 'tsumo':
        for player in game.players:
            if player.id != winner.id:
                player.money -= payout
                winner.money += payout
    else: # ron
        loser = Player.query.get(loser_id)
        if loser and loser.game_id == game.id:
            loser.money -= payout
            winner.money += payout

    # Apply Dealer/Round logic
    if is_dealer_win:
        game.continues += 1
    else:
        game.continues = 0
        game.dealer_id = (game.dealer_id % 4) + 1
        if game.dealer_id == 1:
            winds = ['East', 'South', 'West', 'North']
            try:
                curr_index = winds.index(game.round_wind)
                game.round_wind = winds[(curr_index + 1) % 4]
            except ValueError:
                game.round_wind = 'East'

    record = RoundRecord(
        game_id=game.id,
        winner_id=winner_id,
        loser_id=loser_id if win_type == 'ron' else None,
        points_exchanged=points,
        win_type=win_type,
        is_dealer_win=is_dealer_win
    )
    db.session.add(record)
    db.session.commit()

    # Emit socket io event
    socketio.emit('game_updated', game.to_dict(), to=room_code)
    
    return jsonify(game.to_dict())


@app.route('/api/game/<room_code>', methods=['DELETE'])
def delete_game(room_code):
    game = Game.query.filter_by(game_code=room_code).first()
    if not game:
        return jsonify({"error": "Game not found"}), 404

    # The cascading deletes set up in models.py will delete associated Players & RoundRecords
    db.session.delete(game)
    db.session.commit()

    # Emit an event to tell any connected clients to leave
    socketio.emit('game_ended', to=room_code)

    return jsonify({"success": True, "message": f"Game {room_code} and its history have been deleted."})


# WebSocket Events
@socketio.on('join_game')
def on_join(data):
    room = data['room_code']
    join_room(room)


@app.route('/api/analyze', methods=['POST'])
def analyze_hand():
    cleanup_old_media_files()

    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        # Generate generic unique ID
        unique_id = str(uuid.uuid4())
        
        # Determine extension and create unique final filename
        ext = original_filename.rsplit('.', 1)[1].lower()
        upload_filename = f"upload_{unique_id}.{ext}"
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], upload_filename)
        file.save(image_path)

        # Generate unique output filename for the generated image
        output_filename = f"result_{unique_id}.png"
        uploaded_image_url = media_url('uploads', upload_filename)
        generated_image_url = media_url('outputs', output_filename)

        # --- Call Your Backend Logic ---
        try:
            others = {
                "round": request.form.get('round', 'east'),
                "dealer": request.form.get('dealer', 'east'),
                "continues": form_int('continues', 0),
                "dice": form_int('dice', 18),
                "seat": request.form.get('seat', 'east'),
                "wins": request.form.get('wins', 'east'),
                "base": form_int('base', 100),
                "bonus": form_int('bonus', 30),
                "concealed": form_bool('concealed'),
                "ready": form_bool('ready'),
                "heavenly_win": form_bool('heavenly_win'),
                "heavenly_win_tai": form_int('heavenly_win_tai', 24),
                "human_win": form_bool('human_win'),
                "human_win_tai": form_int('human_win_tai', 16),
                "earthly_win": form_bool('earthly_win'),
                "earthly_win_tai": form_int('earthly_win_tai', 16),
                "heavenly_ready": form_bool('heavenly_ready'),
                "heavenly_ready_tai": form_int('heavenly_ready_tai', 16),
                "earthly_ready": form_bool('earthly_ready'),
                "earthly_ready_tai": form_int('earthly_ready_tai', 8),
                "seven_robbing_one": form_bool('seven_robbing_one'),
                "seven_robbing_one_tai": form_int('seven_robbing_one_tai', 8),
                "rob_kong": form_bool('rob_kong'),
                "rob_kong_tai": form_int('rob_kong_tai', 1),
                "single_wait": form_bool('single_wait'),
                "half_qiu": form_bool('half_qiu'),
                "kong_draw": form_bool('kong_draw'),
                "kong_draw_tai": form_int('kong_draw_tai', 1),
                "last_discard": form_bool('last_discard'),
                "last_discard_tai": form_int('last_discard_tai', 1),
                "last_tile": form_bool('last_tile'),
                "last_tile_tai": form_int('last_tile_tai', 1),
                "quan_qiu": form_bool('quan_qiu'),
                "see_flower_word": form_bool('see_flower_word'),
                "open_kongs": form_int('open_kongs', 0),
                "concealed_kongs": form_int('concealed_kongs', 0),
                "concealed_triplets": form_int('concealed_triplets', 0),
            }
            final_money, final_breakdown, final_tai_log = final_backend_main(image_path, others_settings=others, output_filename=output_filename)
            
            if not final_breakdown:
                return jsonify({
                    "is_winning": False,
                    "message": "The uploaded hand does not form a winning condition.",
                    "uploaded_image_url": uploaded_image_url
                })
            
            # Future Phase 3 Game Update Logic goes here (e.g. updating DB, socketio.emit)
            
            return jsonify({
                "is_winning": True,
                "money": final_money,
                "breakdown": final_breakdown,
                "tai_log": final_tai_log,
                "uploaded_image_url": uploaded_image_url,
                "generated_image_url": generated_image_url
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

    return jsonify({"error": "Invalid file type"}), 400


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})


# Serve short-lived media files from the runtime media volume.
@app.route('/media/<path:folder>/<path:filename>')
def serve_media(folder, filename):
    if folder == 'uploads':
        response = send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    elif folder == 'outputs':
        response = send_from_directory(app.config['OUTPUT_FOLDER'], filename)
    else:
        return jsonify({"error": "Not found"}), 404

    response.headers['Cache-Control'] = 'no-store'
    return response


# Backward-compatible route for older responses that still reference /static/uploads or /static/outputs.
@app.route('/static/<path:folder>/<path:filename>')
def serve_static(folder, filename):
    if folder == 'uploads':
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    if folder == 'outputs':
        return send_from_directory(app.config['OUTPUT_FOLDER'], filename)
    return jsonify({"error": "Not found"}), 404

if __name__ == '__main__':
    # Create the folders if they don't exist
    ensure_media_dirs()
    socketio.run(app, debug=True, port=5000)
