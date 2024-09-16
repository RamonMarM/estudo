import os
from flask import Flask, render_template, session, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField
from wtforms.validators import DataRequired
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'
app.config['SQLALCHEMY_DATABASE_URI'] =\
    'sqlite:///' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

bootstrap = Bootstrap(app)
moment = Moment(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

DISC = [('DSWA5', 'DSWA5'), ('GPSA5', 'GPSA5'), ('IHCA5', 'IHCA5'), ('SODA5', 'SODA5'), ('PJIA5', 'PJIA5'), ('TCOA5', 'TCOA5')]

class NameForm(FlaskForm):
    name = StringField('Nome do professor:', validators=[DataRequired()])
    disc = SelectField('Disciplina:', choices=DISC, validators=[DataRequired()])
    submit = SubmitField('Submit')

class Disc(db.Model):
    __tablename__ = 'discs'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='disc', lazy='dynamic')

    def __repr__(self):
        return '<Disc %r>' % self.name

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    disc_id = db.Column(db.Integer, db.ForeignKey('discs.id'))

    def __repr__(self):
        return '<User %r>' % self.username

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Disc=Disc)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/')
def index():
    return render_template('index.html', current_time=datetime.utcnow())

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    form = NameForm()

    if form.validate_on_submit():
        print(f"Form data: Name={form.name.data}, Disc={form.disc.data}")

        # Verifica se o usuário já existe
        user = User.query.filter_by(username=form.name.data).first()
        
        # Verifica se a disciplina já existe
        user_disc = Disc.query.filter_by(name=form.disc.data).first()
        
        if user is None:
            # Se o usuário não existe, cria um novo usuário e disciplina
            if user_disc is None:
                user_disc = Disc(name=form.disc.data)
                db.session.add(user_disc)
                print(f"Added new disc: {user_disc}")
            
            # Cria e adiciona um novo usuário
            user = User(username=form.name.data, disc=user_disc)
            db.session.add(user)
            print(f"Added new user: {user}")
            session['known'] = False
        else:
            # Se o usuário já existe, atualiza a disciplina
            if user_disc is None:
                user_disc = Disc(name=form.disc.data)
                db.session.add(user_disc)
                print(f"Added new disc: {user_disc}")
            user.disc = user_disc
            print(f"Updated user disc: {user}")
            session['known'] = True
        
        db.session.commit()  # Comita as alterações no banco de dados

        session['name'] = form.name.data
        session['disc'] = form.disc.data
        return redirect(url_for('professores'))

    return render_template('cadastro.html', form=form, name=session.get('name'),
                           known=session.get('known', False))


@app.route('/professores', methods=['GET', 'POST'])
def professores():
    user_all = User.query.all()
    discs = Disc.query.all()
   
    return render_template('professores.html', user_all=user_all, discs=discs)


if __name__ == '__main__':
    app.run(debug=True)
