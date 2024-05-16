from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_restful import Api, Resource
from datetime import datetime 
import re


app = Flask(__name__, static_url_path="/static")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/mariadoloressoleramarquez/BOOTCAMP-W10-PYTHON/Flask-API/data/filmflix.db'

db = SQLAlchemy(app)
api = Api(app)


class Film(db.Model):
    __tablename__ = 'tblFilms'  # Ensure the table name matches the one in your database
    filmID = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    yearReleased = db.Column(db.Integer)
    rating = db.Column(db.Float)
    duration = db.Column(db.Integer)
    genre = db.Column(db.String(255))

    def __repr__(self):
        return f"<Film {self.filmID}: {self.title}>"

# Existing routes for rendering HTML pages and handlers endpoints

@app.route("/")
def base():
    return render_template("base.html")



        # Validation check for yearReleased
       
@app.route("/add", methods=["GET", "POST"])
def add():
    if request.method == "POST":
        title = request.form.get('title')
        
        # Check if 'rating' field is present in the form data
        rating_str = request.form.get('rating')
        if rating_str is None:
            return "Rating is required."

        try:
            rating = int(rating_str)
        except ValueError:
            return "Invalid rating. Please enter a valid number."

        duration_str = request.form.get('duration')
        genre = request.form.get('genre')

        current_year = datetime.now().year

        if request.headers['Content-Type'] == 'application/json':
            # Handle JSON data
            data = request.json
            year_released_str = data.get('yearReleased')
        elif request.headers['Content-Type'] == 'application/x-www-form-urlencoded':
            # Handle form data
            year_released_str = request.form.get('yearReleased')
        else:
            return "Unsupported Media Type", 415

        try:
            if year_released_str is not None:
                year_released = int(year_released_str)
            else:
                return "Year released is required."
        except ValueError as e:
            print(f"Error converting 'yearReleased' to int: {e}")
            return "Internal Server Error", 500

        # Validate the title using a regular expression
        if not all(word.isalpha() or word.isspace() for word in title.split()):
            return "Invalid characters in the title. Please use only letters and spaces."

        if not (1 <= rating <= 5):
            return "Invalid rating. Please enter a number between 1 and 5."

        if duration_str is not None:
            try:
                duration = int(duration_str)
                if duration < 1:
                    return "Invalid duration. Please enter a positive number."
            except ValueError:
                return "Invalid duration. Please enter a valid number."

        # Validation check for genre
        if genre is not None and not all(word.isalpha() or word.isspace() for word in genre.split()):
            return "Invalid characters in the genre. Please use only letters and spaces."

        # If all validation passes, add the film to the database
        new_film = Film(title=title, yearReleased=year_released, rating=rating, duration=duration, genre=genre)
        db.session.add(new_film)
        db.session.commit()

        return redirect(url_for('read'))  # Redirect to the read page after adding the film
    else:
        return render_template("add.html")



@app.route("/delete", methods=["GET", "POST"])
def delete():
    if request.method == "POST":
        film_id = request.form.get('filmID')

        if film_id is None:
            return "FilmID is required for deletion."

        try:
            film_id = int(film_id)
        except ValueError:
            return "Invalid FilmID. Please enter a valid number."

        film_to_delete = Film.query.get(film_id)

        if film_to_delete:
            db.session.delete(film_to_delete)
            db.session.commit()
            return redirect(url_for('read'))  # Redirect to the read page after deletion
        else:
            return "Film not found."

    else:
        return render_template("delete.html")



@app.route("/menu", methods=["GET"])
def menu():
    return render_template("menu.html")



@app.route("/update", methods=["GET", "POST"])
def update():
    if request.method == "POST":
        film_id = request.form.get('filmID')
        film = Film.query.get(film_id)

        if film:
            field_to_update = request.form.get('field')
            new_value = request.form.get('newValue')

            # Update the chosen field with the new value
            setattr(film, field_to_update, new_value)

            db.session.commit()
            return redirect(url_for('read'))  # Redirect to the read page after updating the film
        else:
            return "Film not found."

    return render_template("update.html")



@app.route("/list", methods=["GET"])
def read():
    if request.method == "GET":
        # Fetch all films from the database
        films = Film.query.all()
        return render_template("list.html", films=films)
    else:
        # Handle other methods if needed
        return render_template("list.html")



@app.route("/exit", methods=["GET"])
def exit():
        return render_template("exit.html")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")


# Create your API resources
class FilmResource(Resource):
    def get(self, film_id):
        film = Film.query.get_or_404(film_id)
        # You can customize the response format as needed
        return {'filmID': film.filmID, 'title': film.title, 'year': film.year, 'rating': film.rating,
                'duration': film.duration, 'genre': film.genre}

    def delete(self, film_id):
        film = Film.query.get_or_404(film_id)
        db.session.delete(film)
        db.session.commit()
        return '', 204

class FilmListResource(Resource):
    def get(self):
        films = Film.query.all()
        return [{'filmID': film.filmID, 'title': film.title, 'year': film.year, 'rating': film.rating,
                 'duration': film.duration, 'genre': film.genre} for film in films]

    def post(self):
        data = request.get_json()
        new_film = Film(title=data.get('title'), year=data.get('year'), rating=data.get('rating'),
                        duration=data.get('duration'), genre=data.get('genre'))
        db.session.add(new_film)
        db.session.commit()
        return {'filmID': new_film.filmID, 'title': new_film.title, 'year': new_film.year,
                'rating': new_film.rating, 'duration': new_film.duration, 'genre': new_film.genre}, 201

# Add resources to the API
api.add_resource(FilmListResource, '/films')
api.add_resource(FilmResource, '/films/<int:film_id>')

if __name__ == '__main__':
    with app.app_context():
        # Create the database tables
        db.create_all()
    # Run the Flask app
    app.run(debug=True, host="0.0.0.0",  pin_security=True)
