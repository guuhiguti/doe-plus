from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_user, logout_user

from extensions import db
from models import DEFAULT_CATALOG, CatalogItem, Organization, User, _now

auth_blueprint = Blueprint("auth", __name__)


@auth_blueprint.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            flash("E-mail ou senha inválidos.", "error")
            return render_template("auth/login.html", email=email)

        login_user(user)
        user.last_login_at = _now()
        db.session.commit()
        return redirect(url_for("main.dashboard"))

    return render_template("auth/login.html")


@auth_blueprint.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        organization_name = request.form["organization_name"].strip()
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if User.query.filter_by(email=email).first():
            flash("Já existe uma conta com esse e-mail.", "error")
            return render_template(
                "auth/register.html",
                organization_name=organization_name,
                name=name,
                email=email,
            )

        organization = Organization(name=organization_name)
        db.session.add(organization)
        db.session.flush()

        for category, item_name in DEFAULT_CATALOG:
            db.session.add(CatalogItem(organization_id=organization.id, category=category, name=item_name))

        user = User(organization_id=organization.id, name=name, email=email, is_owner=True)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        return redirect(url_for("main.dashboard"))

    return render_template("auth/register.html")


@auth_blueprint.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.index"))
