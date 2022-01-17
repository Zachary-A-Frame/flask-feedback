from flask import Flask, render_template, redirect, session
from flask_debugtoolbar import DebugToolbarExtension
from importlib_metadata import email
from werkzeug.exceptions import Unauthorized
from password import password
from models import connect_db, db, User, Feedback
from forms import RegisterForm, LoginForm, FeedbackForm, DeleteForm

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://postgres:{password}@localhost:5432/feedback_exercise"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = "cupcakezrcoolz"
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

toolbar = DebugToolbarExtension(app)

connect_db(app)


@app.route("/")
def homepage():
    """Homepage of site; redirect to register."""

    return redirect("/register")


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register a user: produce form and handle form submission."""

    if "username" in session:
        return redirect(f"/users/{session['username']}")

    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        # Now we take our validated data from our form fields and create a new instance of the class User.
        user = User.register(username=username, password=password, email=email, first_name=first_name, last_name=last_name)
        # Next we need to add our user to our session and commit to our database.
        db.session.commit()
        session['username'] = user.username
        #  We then redirect to our user's page.
        return redirect(f"/users/{user.username}")
    # Or else we return to the register form.
    else:
        return render_template("users/register.html", form=form)



@app.route('/login', methods=['GET', 'POST'])
def login():
    """Produce login form or handle login."""

    # Checks if username is in session, then redirects us to the user's page.
    if "username" in session:
        return redirect(f"/users/{session['username']}")

    # Variable for grabbing data from our login form.
    form = LoginForm()
    # If form is submitted, grab data
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
    # We authenticate the user's information, or we display an error. We'll flash an error here if our data is incorrect. If our info is right it redirects us to the users page.
        user = User.authenticate(username, password)  # <User> or False
        if user:
            session['username'] = user.username
            return redirect(f"/users/{user.username}")
        else:
            form.username.errors = ["Invalid username/password."]
            return render_template("users/login.html", form=form)

    return render_template("users/login.html", form=form)


@app.route("/logout")
def logout():
    """Logout route."""
    # If a user wishes to log out, all we have to do is remove them from the session and redirect them to the login page.
    session.pop("username")
    return redirect("/login")


@app.route("/users/<username>")
def show_user(username):
    """Example page for logged-in-users."""
    # We'll be using this next line a lot, if we don't have the user in our session then it redirects them.
    if "username" not in session or username != session['username']:
        raise Unauthorized()
    # We query our db, get their username. We declare our Delete form, which is blank.
    user = User.query.get(username)
    form = DeleteForm()

    return render_template("users/show.html", user=user, form=form)

@app.route("/users/<username>/delete", methods=["POST"])
def remove_user(username):
    """Remove user and redirect to login."""
    if "username" not in session or username != session['username']:
        raise Unauthorized()

    user = User.query.get(username)
    db.session.delete(user)
    db.session.commit()
    session.pop("username")

    return redirect("/login")

@app.route("/users/<username>/feedback/new", methods=["GET", "POST"])
def new_feedback(username):
    """Show add-feedback form and process it."""
    if "username" not in session or username != session['username']:
        raise Unauthorized()
    # We need data from our feedback form.
    form = FeedbackForm()
    # If form is submitted, grab data
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data
        # Declare a new instance of Feedback model.
        feedback = Feedback(title=title, content=content, username=username)
        # Add that new instance to our session.
        db.session.add(feedback)
        db.session.commit()
        # Redirect back to the user's homepage, or take them back to the new feedback page.
        return redirect(f"/users/{feedback.username}")
    else:
        return render_template("feedback/new.html", form=form)


@app.route("/feedback/<int:feedback_id>/update", methods=["GET", "POST"])
def update_feedback(feedback_id):
    """Show update-feedback form and process it."""
    # We're going to use this pattern in our update and delete posts.
    feedback = Feedback.query.get(feedback_id)

    if "username" not in session or feedback.username != session['username']:
        raise Unauthorized()

    form = FeedbackForm(obj=feedback)

    if form.validate_on_submit():
        feedback.title = form.title.data
        feedback.content = form.content.data

        db.session.commit()

        return redirect(f"/users/{feedback.username}")

    return render_template("/feedback/edit.html", form=form, feedback=feedback)



@app.route("/feedback/<int:feedback_id>/delete", methods=["POST"])
def delete_feedback(feedback_id):
    """Delete feedback."""

    feedback = Feedback.query.get(feedback_id)

    if "username" not in session or feedback.username != session['username']:
        raise Unauthorized()

    form = DeleteForm()

    if form.validate_on_submit():
        db.session.delete(feedback)
        db.session.commit()

    return redirect(f"/users/{feedback.username}")
