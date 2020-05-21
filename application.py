import os

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

userid = None
bookid = None

@app.route("/")
def index():
    global userid
    userid = None
    return render_template("index.html")

@app.route("/log_in")
def log_in():
    return render_template("log_in.html")

@app.route("/sign_up")
def sign_up():
    return render_template("sign_up.html")

@app.route("/log_in_check", methods=["POST"])
def log_in_check():
    global userid
    username = request.form.get("username")
    password = request.form.get("password")
    """ if username is None or password is None:
        return render_template("welcome.html", error=error) """
    userid = db.execute("SELECT userid FROM users WHERE username=:username AND password=:password",
    {"username": username, "password": password}).fetchone()[0]
    if userid is None:
        return render_template("log_in.html", error=True)
    name = db.execute("SELECT name FROM users WHERE username=:username", 
    {"username": username}).fetchone()
    return render_template("welcome.html", name=name[0])

@app.route("/sign_up_check", methods=["POST"])
def sign_up_check():
    global userid
    username = request.form.get("username")
    password = request.form.get("password")
    re_password = request.form.get("re-password")
    name = request.form.get("name")
    email = request.form.get("email_id")
    items = [name, email, username, password]
    error = None
    if ("" in items):
        error="One of the fields is empty."
    elif password != re_password:
        error="Your passwords are different."
    elif db.execute("SELECT * FROM users WHERE username=:username",
    {"username": username}).rowcount != 0:
        error="This username has already been taken."
    else:
        db.execute("INSERT INTO users (name, email, username, password) VALUES (:name, :email, :username, :password)",
        {"name": name, "email": email, "username": username, "password": password})
        db.commit()
        userid = db.execute("SELECT userid FROM users WHERE username=:username",
        {"username": username}).fetchone()[0]
        return render_template("welcome.html", name=name)
    return render_template("sign_up.html", error=error)

@app.route("/search", methods=["POST"])
def search():
    query = '%' + request.form.get("search") + '%'
    results = db.execute("SELECT * FROM books WHERE UPPER(title) LIKE :query OR UPPER(author) LIKE :query OR isbn LIKE :query ORDER BY year",
    {"query": query.upper()}).fetchall()
    return render_template("search.html", results=results)

@app.route("/<string:bookID>")
def book_page(bookID):
    global bookid
    global userid
    bookid = bookID
    book_info = db.execute("SELECT * FROM books WHERE bookid=:bookid",
    {"bookid": bookid}).fetchone()
    reviews = db.execute("SELECT reviews.review, reviews.rating, users.name FROM reviews INNER JOIN users ON reviews.userid=CAST(users.userid AS VARCHAR) WHERE bookid=:bookid",
    {"bookid": bookid}).fetchall()
    ratings = db.execute("SELECT rating FROM reviews WHERE bookid=:bookid",
    {"bookid": bookid}).fetchall()
    num_of_rating = db.execute("SELECT rating FROM reviews WHERE bookid=:bookid",
    {"bookid": bookid}).rowcount
    rating_sum = 0
    average_rating = None
    if num_of_rating != 0:
        for i in ratings:
            rating_sum += int(i[0])
        average_rating = rating_sum / num_of_rating
    already_rated = db.execute("SELECT * FROM reviews WHERE bookid=:bookid AND userid=:userid",
    {"bookid": bookid, "userid": str(userid)}).rowcount != 0

    return render_template("book_page.html", book_info=book_info, reviews=reviews, ratings=ratings,
    num_of_rating=num_of_rating, average_rating=average_rating, already_rated=already_rated, error=False)

@app.route("/new_review", methods = ["POST"])
def new_review():
    global userid
    global bookid
    review = request.form.get("new_review")
    rating = request.form.get("new_rating")
    if review is not None and userid is not None:
        db.execute("INSERT INTO reviews (userid, bookid, rating, review) VALUES (:userid, :bookid, :rating, :review)",
        {"userid": userid, "bookid": bookid, "rating": rating, "review": review})
        db.commit()
        error=False
    else:
        error=True

    
    book_info = db.execute("SELECT * FROM books WHERE bookid=:bookid",
    {"bookid": bookid}).fetchone()
    reviews = db.execute("SELECT reviews.review, reviews.rating, users.name FROM reviews INNER JOIN users ON reviews.userid=CAST(users.userid AS VARCHAR) WHERE bookid=:bookid",
    {"bookid": bookid}).fetchall()
    ratings = db.execute("SELECT rating FROM reviews WHERE bookid=:bookid",
    {"bookid": bookid}).fetchall()
    num_of_rating = db.execute("SELECT rating FROM reviews WHERE bookid=:bookid",
    {"bookid": bookid}).rowcount
    rating_sum = 0
    average_rating = None
    if num_of_rating != 0:
        for i in ratings:
            rating_sum += int(i[0])
        average_rating = rating_sum / num_of_rating
    already_rated = db.execute("SELECT * FROM reviews WHERE bookid=:bookid AND userid=:userid",
    {"bookid": bookid, "userid": str(userid)}).rowcount != 0

    return render_template("book_page.html", book_info=book_info, reviews=reviews, ratings=ratings,
    num_of_rating=num_of_rating, average_rating=average_rating, already_rated=already_rated, error=error)

@app.route("/welcome")
def welcome():
    global userid
    if userid is None:
        return render_template("index.html")
    name = db.execute("SELECT name FROM users WHERE userid=:userid",
    {"userid": userid}).fetchone()[0]
    return render_template("welcome.html", name=name)