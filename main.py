#kod Fake delete metode dodajemo u bazi podataka stupac "Izbrisan" sa vrijednosti True.
    #Zatim filtriramo sve korisnike sa vrijednosti False u tom stupcu pod normalno.
        #Ako zelimo nekoga vratiti u pocetno stanje, stavimo mu vrijednost "False" u stupcu "Izbrisan".

import hashlib
import uuid
import random
from flask import Flask, render_template, request, make_response, redirect, url_for
from models import User, db

app = Flask(__name__)
db.create_all()  # create (new) tables in the database


@app.route("/", methods=["GET"])
def index():
    session_token = request.cookies.get("session_token")

    if session_token:
        user = db.query(User).filter_by(session_token=session_token).first()
    else:
        user = None

    return render_template("index.html", user=user)


@app.route("/login", methods=["POST"])
def login():
    name = request.form.get("user-name")
    email = request.form.get("user-email")
    password = request.form.get("user-password")

    #password je varijabla

    #sada slijedi hashing password-a

    hashed_password = hashlib.sha256(password.encode()).hexdigest()


    # create a secret number
    secret_number = random.randint(1, 30)

    # see if user already exists
    user = db.query(User).filter_by(email=email).first()

    if not user:
        # create a User object
        user = User(name=name, email=email, secret_number=secret_number, password=hashed_password)
        user.save()

    if hashed_password != user.password:
        return "Wrong password! Go back and try again."

    elif hashed_password == user.password:
        session_token = str(uuid.uuid4())

        user.session_token = session_token
        user.save()

        response = make_response(redirect(url_for("index")))
        response.set_cookie("session_token", session_token, httponly=True, samesite="Strict")

        return response

@app.route("/result", methods=["POST"])
def result():
    guess = int(request.form.get("guess"))

    session_token = request.cookies.get("session_token")

    # get user from the database based on her/his session_token
    user = db.query(User).filter_by(session_token=session_token).first()

    if guess == user.secret_number:
        message = "Correct! The secret number is {0}".format(str(guess))

        # create a new random secret number
        new_secret = random.randint(1, 30)

        # update the user's secret number
        user.secret_number = new_secret
        user.save()
    elif guess > user.secret_number:
        message = "Your guess is not correct... try something smaller."
    elif guess < user.secret_number:
        message = "Your guess is not correct... try something bigger."

    return render_template("result.html", message=message)




@app.route("/profile", methods=["GET"])
def profile():
    session_token = request.cookies.get("session_token")

    user = db.query(User).filter_by(session_token=session_token, deleted=False).first()

    if user:
        return render_template("profile.html", user=user)
    else:
        return redirect(url_for("index"))

@app.route("/profile/edit", methods=["GET", "POST"])
def profile_edit():

    session_token = request.cookies.get("session_token")

    user = db.query(User).filter_by(session_token=session_token, deleted=False).first()


    if request.method == "GET":
        if user:
            return render_template("profile_edit.html", user=user)
        else:
            return redirect(url_for("index"))


    elif request.method == "POST":
        name = request.form.get("profile-name")
        email = request.form.get("profile-email")

        stara_lozinka = request.form.get("stara-lozinka")
        nova_lozinka = request.form.get("nova-lozinka")

        if stara_lozinka and nova_lozinka:
            hashed_stara_lozinka = hashlib.sha256(stara_lozinka.encode()).hexdigest()
            hashed_nova_lozinka = hashlib.sha256(nova_lozinka.encode()).hexdigest()

            if hashed_stara_lozinka == user.password:

                user.password = hashed_nova_lozinka

            else:

                return "Kriva stara lozinka!"

        #promjena user objecta

        user.name = name
        user.email = email

        user.save()

        return redirect(url_for("profile"))

@app.route("/profile/delete", methods=["GET", "POST"])
def profile_delete():

    session_token = request.cookies.get("session_token")

    user = db.query(User).filter_by(session_token=session_token, deleted=False).first()

    if request.method == "GET":
        if user:
            return render_template("profile_delete.html", user=user)
        else:
            return redirect(url_for("index"))

    elif request.method == "POST":
        user.deleted = True #dodali smo stupac u bazu podataka, osoba koja je izbrisana ima boolean vrijednost "True" u tom stupcu
        user.save()

        return redirect(url_for("index"))


@app.route("/users", methods=["GET"])
def all_users():
    users = db.query(User).filter_by(deleted=False).all()

    return render_template("users.html", users=users)


@app.route("/user/<user_id>", methods=["GET"])
def user_details(user_id):
    user = db.query(User).get(int(user_id))

    return render_template("user_details.html", user=user)


if __name__ == '__main__':
    app.run(use_reloader=True)  # if you use the port parameter, delete it before deploying to Heroku
