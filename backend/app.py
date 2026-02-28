# Imports
import os
import uuid
import random
import string
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit, join_room

from db import db
from src.models import Game, Player, RoundRecord

load_dotenv() # Load environment variables from .env

# Import your core functions from the src package
from src.main import backend_main

# --- Flask App Configuration ---
UPLOAD_FOLDER = 'static/uploads'
OUTPUT_FOLDER = 'static/outputs'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

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

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
            final_money, final_breakdown = backend_main(others, output_filename=output_filename)
            
            # Future Phase 3 Game Update Logic goes here (e.g. updating DB, socketio.emit)
            
            return jsonify({
                "money": final_money,
                "breakdown": final_breakdown,
                "uploaded_image_url": f"/static/uploads/{upload_filename}",
                "generated_image_url": f"/static/outputs/{output_filename}"
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
    socketio.run(app, debug=True, port=5000)
