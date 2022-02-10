from flask import render_template, Response, request, Blueprint, flash, current_app, session, redirect, url_for
from flask_login import current_user, login_user
from flask_cors import cross_origin
import face_recognition
from . import db
from .models import Face, User
import numpy



authFace = Blueprint('authFace', __name__)


#SIGN UP FACE
@authFace.route('/sign-up-face', methods=['POST','GET'])
@cross_origin()
def signUpFace():
    # weryfikacja 1 etapu rejestracji
    if 'id' not in session:
        flash('Sign up first!', category='error')
        current_app.logger.info('Forced to break 1 authentication proces')
        return redirect(url_for('auth.sign_up'))
    
    # weryfikacja czy użytkownik nie posiada już encodings w bazie danych
    user = User.query.filter( User.id == session['id'] ).first()
    encoID = Face.query.filter( Face.user_id == session['id'] ).first()
    if encoID:
        flash('we already have your face features')
        current_app.logger.info('double registration attempt')
        return redirect(url_for('authFace.loginFace'))
        
    # 2 etap rejestracji - przetwarzanie żądania
    if request.method == 'POST':
        request_data = request.get_json()
        encodings = request_data['encodings']

        # puste żądanie - brak encodings
        if encodings == 'undefined':
            current_app.logger.info(f'POST request empty')
            flash("We recived no data, try again!", category='error')
            return Response(status=204)

        # encodings przesłane pomyślnie, zapisanie json'a w bazie, ukończenie 2 etapu
        else:            
            new_encodings = Face( face_encodings = request_data, user_id = session['id'] )
            db.session.add(new_encodings)
            db.session.commit()
            login_user(user)
            flash("Congratulations, you have completed the registration process!", category='success')
            return Response(status=200)

    return render_template('sign_up_face.html', user=current_user)
    
            

#LOGIN FACE
@authFace.route('/login-face',methods=['POST','GET'])
@cross_origin()
def loginFace():
    # weryfikacja 1 etapu logowania
    if 'id' not in session:
        current_app.logger.info('impostor detected')
        flash('log in first!', category='error')
        return redirect(url_for('auth.login'))
    
    # przekierowanie zalogowanego użytkownika
    if current_user.is_authenticated:
        flash('you don\'t need to log in twice.', category='error')
        return redirect(url_for('views.home'))
    
    # wyszukanie użytkownika po user ID, pobranie encodings z bazy
    encoID = Face.query.filter( Face.user_id == session['id'] ).first()
    user = User.query.filter( User.id == session['id'] ).first()

    # Pobranie encodings należących do użytkownika.
    if encoID:
        jsonDB = encoID.face_encodings
        encodingsDB = jsonDB['encodings']
    
    # Brak encodings oznacza nieukończony proces logowania.
    else:
        current_app.logger.info(f'{user} not fully registred')
        flash("please complete the registration process!", category='error')
        return redirect(url_for('authFace.signUpFace')) # przekierowanie do sign-up-face

    # 2 etap logowania - przetwarzanie żądania 
    if request.method == 'POST':
        request_data = request.get_json()
        encodings = request_data['encodings']

        # puste żądanie - brak encodings
        if encodings == 'undefined':
            current_app.logger.info(f'POST request empty from {user}')
            flash("we can't see you, no data recived!", category='error')
            return Response(status=204)     # fail response - powtórzenie całego procesu

        # encodings przesłane pomyślnie, weryfikacja tożsamości     
        else:
            # alagorytm przetwarzający encodings dictionary -> numpy array
            decodedEncodings = numpy.array([])
            decodedEncodingsDB = numpy.array([])

            for key in encodings.keys():
                decodedEncodings = numpy.append(decodedEncodings, encodings.get(key))       # tworzenie tablicy dla enco klienta
                decodedEncodingsDB = numpy.append(decodedEncodingsDB, encodingsDB.get(key)) # tworzenie tablicy dla enco z bazy

            # Porównanie twarzy - wyznaczanie odległości euklidesowej
            matches = face_recognition.compare_faces([decodedEncodings], decodedEncodingsDB)

            # pomyślne logowanie
            if True in matches:
                flash('Welcom Back!', category='success')
                current_app.logger.info(f'successful login for {user}')
                login_user(user)            # zalogowanie użytkownika - 2 etap logowania
                return Response(status=200) # success response - przekierowanie zalogowanego użytkownika do Home

            # błędne logowanie, można traktować jako próbę włamania.
            elif False in matches:
                session.clear()             # wyczyszczenie sesji
                session['impostor'] = request.environ['REMOTE_ADDR']
                hacker = session['impostor']
                current_app.logger.info(f'faces don\t match for {user}. Account may be at risk ip:{hacker}')
                return Response(status=401) # impostor response - przekierowanie do strony głównej
    
    return render_template("login_face.html", user = current_user)