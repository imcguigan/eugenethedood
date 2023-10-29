from flask import Flask, request, redirect, url_for, session, flash, render_template
from functools import wraps
import os
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import boto3


s3 = boto3.client(
    "s3",
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    region_name="us-east-2",  # Adjust this if you're using a different AWS region for your S3 bucket
)

load_dotenv()

app = Flask(__name__)  # runs the app
app.debug = True
S3_LOCATION = "https://eugenethedood.s3.us-east-2.amazonaws.com/"


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(
    BASE_DIR, "eugenedood.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


app.secret_key = os.environ.get("FLASK_SECRET_KEY")
admin_username = os.environ.get("ADMIN_USERNAME")
admin_password = os.environ.get("ADMIN_PASSWORD")


# Check to see if user is logged into admin site. If not redirects them to gallery
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" not in session:
            flash("Please log in to access this page.", "danger")
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)

    return decorated_function


@app.route("/")
def gallery():
    latest_image = Image.query.order_by(Image.uploaded_at.desc()).first()
    all_images = Image.query.order_by(Image.uploaded_at.desc()).all()[1:6]
    return render_template(
        "gallery.html",
        latest_image=latest_image,
        all_images=all_images,
        S3_LOCATION=S3_LOCATION,
    )


@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session["logged_in"] = True
            session["username"] = user.username
            flash("Logged in successfully!", "success")
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid credentials. Please try again.", "danger")
    return render_template("admin-login.html")


@app.route("/admin-dashboard")
@login_required  # This protects the route for only logged in users
def admin_dashboard():
    return render_template("admin-dashboard.html")


@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    session.pop("username", None)
    flash("Logged out successfully!", "success")
    return redirect(url_for("gallery"))


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return "No file part"

    file = request.files["file"]

    if file.filename == "":
        return "No selected file"

    if file:
        filename = file.filename

        s3.upload_fileobj(
            file,
            os.environ.get("AWS_S3_BUCKET"),
            filename,
            ExtraArgs={"ContentType": file.content_type},
        )
        image_url = f"{S3_LOCATION}{filename}"

        title = request.form.get("image_title", file.filename)

        logged_in_username = session.get("username")
        user = User.query.filter_by(username=logged_in_username).first()
        if not user:
            flash("User not found!", "danger")
            return redirect(url_for("admin_dashboard"))

        new_image = Image(title=title, filename=filename, user_id=user.id)
        db.session.add(new_image)
        db.session.commit()
        return redirect(url_for("admin_dashboard"))


# DB model for image upload
class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    filename = db.Column(db.String(120), nullable=False)
    likes = db.Column(db.Integer, default=0)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)


# DB modael for users
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    images = db.relationship("Image", backref="uploader", lazy=True)


def hash_password(password):
    return generate_password_hash(password)


def check_password(hashed_password, password):
    return check_password_hash(hashed_password, password)


app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///eugenedood.db"
)
