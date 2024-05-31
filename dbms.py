from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import case,func,or_,create_engine

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqldb://root:@localhost:4306/nba'
engine = create_engine("mysql+pymysql://root:@localhost/nba", pool_pre_ping=True)  # SQLite database
db = SQLAlchemy(app)

# Define models


class Team(db.Model):
    __tablename__ = 'team'
    team_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(20), nullable=False)
    city = db.Column(db.String(20), nullable=False)
    year_founded = db.Column(db.Integer, nullable=False)

    def __init__(self, name, city, year_founded):
        self.name = name
        self.city = city
        self.year_founded = year_founded
class Game(db.Model):
    __tablename__ = 'game'
    game_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    team_id_visitor = db.Column(db.Integer, db.ForeignKey('team.team_id'), nullable=False)
    team_id_home = db.Column(db.Integer, db.ForeignKey('team.team_id'), nullable=False)
    winner = db.Column(db.Integer, db.ForeignKey('team.team_id'))
    score_margin = db.Column(db.Integer)

    def __init__(self, team_id_visitor, team_id_home, winner, score_margin):
        self.team_id_visitor = team_id_visitor
        self.team_id_home = team_id_home
        self.winner = winner
        self.score_margin = score_margin
class Player(db.Model):
    __tablename__ = 'player_info'
    person_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(40), nullable=False)
    height = db.Column(db.Float, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    team_id=db.Column(db.Integer)

    def __init__(self, name, country, height, weight,team_id):
        self.name = name
        self.country = country
        self.height = height
        self.weight = weight
        self.team_id=team_id
# Routes
@app.route('/')
def index():
    teams = Team.query.all()
    team_ids = [team.team_id for team in teams]
    return render_template('index1.html',team_ids=team_ids)

@app.route('/teams', methods=['GET', 'POST'])
def teams():
    if request.method == 'POST':
        team_name = request.form['name']
        city = request.form['city']
        year_founded = request.form['country']
        coach = request.form['coach']

        new_team = Team(name=team_name, city=city, year_founded=year_founded, coach=coach)
        db.session.add(new_team)
        db.session.commit()

    teams = Team.query.all()
    return render_template('teams.html', teams=teams)

@app.route('/games', methods=['GET', 'POST'])
def games():
    if request.method == 'POST':
        # Get form data
        team_id_home = request.form['team_id_home']
        team_id_visitor = request.form['team_id_visitor']
        score_margin = request.form['score_margin']
        winner = request.form['winner_id']

        # Create a new game with the provided data
        new_game = Game(team_id_home=team_id_home, away_team_id=team_id_visitor, score_margin=score_margin)

        # Set the winner based on the selected option
        if winner_id and winner_id != "Tie":
            new_game.winner_id = winner_id
        else:
            new_game.winner_id = None  # Tie
        
        # Add the new game to the database session
        db.session.add(new_game)
        db.session.commit()
        

    # Query the database to retrieve all teams
    teams = Team.query.all()

    # Retrieve existing games from the database
    games = Game.query.all()

    return render_template('games.html', teams=teams, games=games)
@app.route('/game_stats')
def game_stats():
    # Query game statistics
    game_stats = db.session.query(
        Team.name.label('team_name'),
        func.count(Game.game_id).label('total_games_played'),
        func.sum(case((Game.winner == Team.team_id, 1), else_=0)).label('total_wins'),
        func.avg(Game.score_margin).label('average_score_margin')
    ).outerjoin(Game, or_(Team.team_id == Game.team_id_home, Team.team_id == Game.team_id_visitor)).group_by(Team.team_id).all()

    return render_template('game_stats.html', game_stats=game_stats)
@app.route('/point_table')
def point_table():
    # Query for point table
    point_table = db.session.query(
        Team.name.label('team_name'),
        func.count().label('total_games_played'),
        func.sum(
            case(
                (Game.winner == Team.team_id, 1),
                else_=0
            )
        ).label('total_points')
    ).outerjoin(
        Game, 
        or_(Team.team_id == Game.team_id_home, Team.team_id == Game.team_id_visitor)
    ).group_by(Team.team_id).all()

    return render_template('point_table.html', team_standings=point_table)
@app.route('/team_players/<int:team_id>',methods=['GET','POST'])
def team_players(team_id):
    # Query for team
    team = Team.query.get(team_id)
    
    if request.method == 'POST':
        # Get player information from the form
        player_names = request.form.getlist('player_name')  # Assuming player names are submitted as a list
        
        # Create player instances and add them to the database session
        players = [Player(name=name, team_id=team_id) for name in player_names]
        db.session.add_all(players)
        db.session.commit()
    
    # Query for players in the team after insertion
    players = Player.query.filter_by(team_id=team_id).all()
    
    return render_template('team_players.html', team=team, players=players)
@app.route('/participating_countries')
def participating_countries():
    result = db.session.query(Player.country, db.func.count(Player.name)).group_by(Player.country).all()
    stats = [{'country': country, 'player_count': count} for country, count in result]
    return render_template('participating_countries.html',stats=stats)
@app.route('/home_winners')
def home_winners():
    query_result = db.session.query(Team.name, Team.city, Game.score_margin, db.func.count(Game.winner))\
                    .join(Game, Team.team_id == Game.team_id_home)\
                    .group_by(Team.name)\
                    .all()
    return render_template('home_winner.html', stats=query_result)


if __name__ == '__main__':
    with app.app_context():
        # Create database tables
        db.create_all()
    # Run the Flask application
    app.run(debug=True)
