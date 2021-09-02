from flask import Flask,render_template,request,session,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import or_
from datetime import datetime
import json

with open('config.json', 'r') as c:
    params = json.load(c)["params"]

local_server=True
app = Flask(__name__)
app.secret_key = 'super-secret-key'
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_uri']
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'u_login'

class Feedback(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(12), nullable=False)
    message = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(12), nullable=True)

class Songs(db.Model):
    sno = db.Column(db.Integer, primary_key=True)
    track = db.Column(db.String(100), nullable=False)
    artist = db.Column(db.String(100), nullable=False)
    album = db.Column(db.String(100), nullable=False)
    genre = db.Column(db.String(100), nullable=False)
    year = db.Column(db.String(100), nullable=False)
    link = db.Column(db.String(500), nullable=False)
    slug = db.Column(db.String(30), nullable=False)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    

@app.route('/')
def home_page():
    songs = Songs.query.filter_by().all()[0:6]
    return render_template('index.html', params=params, songs=songs)

@app.route('/songs', methods=['GET','POST'])
def soundtrack():
    if request.method == 'POST':
        form = request.form
        search_value = form['search_string']
        search = "%{0}%".format(search_value)
        songs = Songs.query.filter(or_(Songs.track.like(search),
                                       Songs.album.like(search),
                                       Songs.artist.like(search),
                                       Songs.genre.like(search),
                                       Songs.year.like(search))).all()
        return render_template('soundtrack.html', params=params, songs=songs)
    else:
        songs = Songs.query.filter_by().all()
        return render_template('soundtrack.html', params=params, songs=songs)


@app.route("/song/<string:song_slug>/", methods=['GET'])
def song_route(song_slug):
    song = Songs.query.filter_by(slug=song_slug).first()
    return render_template('song.html', params=params, song=song)


@app.route('/album/1', methods=['GET','POST'])
def album1():
    s_value= request.form.get("hialbum")
    song = Songs.query.filter_by(album=s_value).first()
    return render_template('hotelcalifornia.html', params=params, song=song)

    
@app.route("/dashboard", methods = ['GET', 'POST'])
def dashboard():
    if "user" in session and session['user']==params['admin_user']:
        songs = Songs.query.all()
        return render_template("dashboard.html", params=params, songs=songs)

    if request.method=="POST":
        username = request.form.get("uname")
        userpass = request.form.get("pass")
        if username==params['admin_user'] and userpass==params['admin_password']:
            # set the session variable
            session['user']=username
            songs = Songs.query.all()
            return render_template("dashboard.html", params=params, songs=songs)

    else:
        return render_template("login.html", params=params)


@app.route("/edit/<string:sno>" , methods=['GET', 'POST'])
def edit(sno):
    if ("user" in session and session['user']==params['admin_user']):
        if request.method=='POST':
            box_track = request.form.get('track')
            artist = request.form.get('artist')
            album = request.form.get('album')
            genre = request.form.get('genre')
            year = request.form.get('year')
            link = request.form.get('link')
            slug = request.form.get('slug')
            if sno=='0':
                song = Songs(track=box_track, artist=artist, album=album, genre=genre, year=year, link=link, slug=slug)
                db.session.add(song)
                db.session.commit()
                return redirect('/dashboard')
            else:
                song = Songs.query.filter_by(sno=sno).first()
                song.track = box_track
                song.artist = artist
                song.album = album
                song.genre = genre
                song.year = year
                song.link = link
                song.slug = slug
                db.session.commit()
                return redirect('/edit/'+sno)

    song = Songs.query.filter_by(sno=sno).first()
    return render_template('edit.html', params=params, song=song, sno=sno)

@app.route("/delete/<string:sno>" , methods=['GET', 'POST'])
def delete(sno):
    if ("user" in session and session['user']==params['admin_user']):
        song = Songs.query.filter_by(sno=sno).first()
        db.session.delete(song)
        db.session.commit()
    return redirect('/dashboard')

@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route('/u_logout')
@login_required
def u_logout():
    logout_user()
    return redirect(url_for('u_login'))
    

@app.route("/contact", methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Feedback(name=name, email = email, phone = phone, message = message, date= datetime.now())
        db.session.add(entry)
        db.session.commit()
        
    songs = Songs.query.filter_by().all()[0:6]
    return render_template('index.html', params=params, songs=songs)


@app.route('/u_login', methods=['GET', 'POST'])
def u_login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect(url_for('u_dashboard'))

        return '<h1>Invalid username or password</h1>'
        #return '<h1>' + form.username.data + ' ' + form.password.data + '</h1>'

    return render_template('u_login.html', params=params,form=form)


@app.route('/u_signup', methods=['GET', 'POST'])
def u_signup():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return '<h1>New user has been created!</h1>'
        #return '<h1>' + form.username.data + ' ' + form.email.data + ' ' + form.password.data + '</h1>'

    return render_template('u_signup.html', params=params,form=form)

@app.route('/u_dashboard', methods=['GET'])
def u_dashboard():
    if request.method == 'POST':
        form = request.form
        search_value = form['search_string']
        search = "%{0}%".format(search_value)
        songs = Songs.query.filter(or_(Songs.track.like(search),
                                       Songs.album.like(search),
                                       Songs.artist.like(search),
                                       Songs.genre.like(search),
                                       Songs.year.like(search))).all()
        return render_template('u_dashboard.html', params=params, songs=songs,name=current_user.username)
    else:
        songs = Songs.query.filter_by().all()
        return render_template('u_dashboard.html', params=params, songs=songs,name=current_user.username)


if __name__ == '__main__':
    app.run()