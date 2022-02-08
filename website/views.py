from flask import Blueprint, render_template, request, flash, jsonify, session, redirect, url_for
from flask_login import login_required, current_user, logout_user
from .models import Note, Face, User
from . import db
import json
from sqlalchemy import delete

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        note = request.form.get('note')

        if len(note) < 1:
            flash('Note is too short!', category='error')
            
        else:
            new_note = Note( data=note, user_id=current_user.id )
            db.session.add(new_note)
            db.session.commit()
            flash('Note added!', category='success')

    return render_template("home.html", user=current_user)


@views.route('/delete-note', methods=['POST'])
@login_required
def delete_note():
    # Odwołanie do konkretnej notatki
    note = json.loads(request.data)
    noteId = note['noteId']
    note = Note.query.get(noteId)

    # Usunięcie notatki
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})


@views.route('/delete-account')
@login_required
def delete_account():
    # Usunięcie wszystkich danych użytkownika
    noteR = delete(Note).where( Note.user_id == current_user.id )
    faceR = delete(Face).where( Face.user_id == current_user.id )
    userR = delete(User).where( User.id == current_user.id )

    db.session.execute(noteR)
    db.session.execute(faceR)
    db.session.execute(userR)
    db.session.commit()

    logout_user()   # wylogowanie użytkownika
    session.clear() # usunięcie sesji
    return redirect(url_for('auth.login'))






