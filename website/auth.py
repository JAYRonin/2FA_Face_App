from distutils.log import error
from flask import Blueprint, render_template, request, flash, redirect, url_for, session, current_app
from sqlalchemy import true
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_required, logout_user, current_user
from .models import User
from . import db
import re


auth = Blueprint('auth', __name__)

#LOGIN
@auth.route('/login', methods=['GET', 'POST'])
def login():
    session.permanent = True
    # przekierowanie zalogowanego użytkownika
    if current_user.is_authenticated:
        flash('you don\'t need to log in twice.', category='error')
        return redirect(url_for('views.home'))
    
    # klient próbujący wysyłać żądania POST mimo zablokowania
    if 'impostor' in session:
        hacker = session['impostor']
        flash('do not refresh the page', category='error')
        current_app.logger.info(f'Potential brute force attack detected for {hacker}') # wiele żądań może świadczyć o ataku brute force
        return render_template("login.html", user=current_user)

    # przetwarzanie żądania
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by( email=email ).first() # znalezienie użytkownika w bazie

        # porównanie hashy haseł, 1 etap logowania
        if user:
            if check_password_hash(user.password, password):
                flash('ok, now look to the camera.', category='success')
                session['id'] = user.id                    # Nadanie ID użytkownika w sesji, świadczy o autoryzacji 1 etapu
                return redirect(url_for('authFace.loginFace'))

        # logika odpowiedzialna za zablokowanie po 3 nieudanych próbach logowania
            else:
                flash('Wrong credentials!', category='error')
                if 'attempts' not in session:
                    session['attempts'] = 1 
                else:
                    attempts = session['attempts']
                    attempts += 1
                    session['attempts'] = attempts
                    if session['attempts'] == 3:
                        session['impostor'] = request.environ['REMOTE_ADDR']
                        flash('Come back in 5 minutes!')
                        return render_template("login.html", user=current_user)

        else:
            flash('Wrong credentials!', category='error')
            if 'attempts' not in session:
                session['attempts'] = 1 
            else:
                attempts = session['attempts']
                attempts += 1
                session['attempts'] = attempts
                if session['attempts'] == 3:
                    session['impostor'] = request.environ['REMOTE_ADDR'] # Nadanie kategorii impostor wraz z adresem IP w sesji, świadczy o zablokowaniu klienta
                    flash('Come back in 5 minutes!')
                    return render_template("login.html", user=current_user)

    return render_template("login.html", user=current_user)

#LOGOUT
@auth.route('/logout')
@login_required
def logout():
    logout_user()   # wylogowanie użytkownika
    session.clear() # usunięcie sesji
    return redirect(url_for('auth.login'))

#SIGN UP
@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    # przekierowanie zarejestorwanego użytkownika
    if current_user.is_authenticated:
        flash('you already have an account.', category='error')
        return redirect(url_for('views.home'))

    # przetwarzanie żądania
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

        user = User.query.filter_by( email=email ).first()
        if user:
            flash('Email already exists.', category='error')
        elif not re.search("([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)", email):
            flash('Invalid email address.', category='error')

        elif len(first_name) < 2 and len(first_name) > 20:
            flash('Provide a real name', category='error')

        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')

        elif len(password1) < 8:
            flash('Password must be at least 8 characters.', category='error')
        
        # poprawne dane, ukończenie 1 etapu rejestracji
        else:
            new_user = User( email=email, first_name=first_name, password=generate_password_hash(
                password1, method='pbkdf2:sha512:120000') ) # Generowanie hashu hasła 

            db.session.add(new_user)
            db.session.commit()
            session['id'] = new_user.id
            flash('great, now we need your face characteristics!', category='success')
            return redirect(url_for('authFace.signUpFace'))

    return render_template("sign_up.html", user=current_user)