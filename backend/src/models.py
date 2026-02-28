from db import db

class Game(db.Model):
    __tablename__ = 'games'
    id = db.Column(db.Integer, primary_key=True)
    game_code = db.Column(db.String(10), unique=True, nullable=False)
    round_wind = db.Column(db.String(20), default='East')
    dealer_id = db.Column(db.Integer, default=1) # 1-4 referring to seat position
    continues = db.Column(db.Integer, default=0)
    
    players = db.relationship('Player', backref='game', lazy=True, cascade="all, delete-orphan")
    rounds = db.relationship('RoundRecord', backref='game', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'game_code': self.game_code,
            'round_wind': self.round_wind,
            'dealer_id': self.dealer_id,
            'continues': self.continues,
            'players': [player.to_dict() for player in self.players],
            'rounds': [r.to_dict() for r in self.rounds]
        }


class Player(db.Model):
    __tablename__ = 'players'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    money = db.Column(db.Integer, default=0)
    seat_position = db.Column(db.Integer, nullable=False) # 1: East, 2: South, 3: West, 4: North

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'money': self.money,
            'seat_position': self.seat_position
        }


class RoundRecord(db.Model):
    __tablename__ = 'round_records'
    id = db.Column(db.Integer, primary_key=True)
    game_id = db.Column(db.Integer, db.ForeignKey('games.id'), nullable=False)
    winner_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True) # Null if draw
    loser_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=True) # Null if self-draw or draw
    points_exchanged = db.Column(db.Integer, default=0)
    win_type = db.Column(db.String(20), nullable=False) # 'ron', 'tsumo', 'draw'
    is_dealer_win = db.Column(db.Boolean, default=False)
    
    # Backref for easier access
    winner = db.relationship('Player', foreign_keys=[winner_id])
    loser = db.relationship('Player', foreign_keys=[loser_id])

    def to_dict(self):
        return {
            'id': self.id,
            'winner_id': self.winner_id,
            'loser_id': self.loser_id,
            'winner_name': self.winner.name if self.winner else None,
            'loser_name': self.loser.name if self.loser else None,
            'points_exchanged': self.points_exchanged,
            'win_type': self.win_type,
            'is_dealer_win': self.is_dealer_win
        }
