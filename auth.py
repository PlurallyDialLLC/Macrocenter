from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash

auth = Blueprint("auth", __name__)

# You will pass your existing database instance into this later
database = None


def init_auth(app, db, login_manager):
    global database
    database = db

    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        user = database.get_user_by_id(user_id)
        if user:
            return User(*user)


class User(UserMixin):
    def __init__(self, id, username, email, password, is_admin=0):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
        self.is_admin = is_admin

# REGISTER
@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]

        hashed = generate_password_hash(password)

        database.create_user(username, email, hashed)

        return redirect(url_for("auth.login"))

    return render_template("register.html")


# LOGIN
@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = database.get_user_by_username(username)

        if user and check_password_hash(user[3], password):
            login_user(User(*user))
            return redirect(url_for("get_all_products"))

        flash("Invalid credentials")

    return render_template("login.html")


# LOGOUT
@auth.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
