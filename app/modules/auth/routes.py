# app/modules/auth/routes.py
from flask import render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from . import auth_bp
from .forms import LoginForm, RegisterForm
from .services import AuthService


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = AuthService.authenticate(form.email.data, form.password.data)
        if user:
            login_user(user)
            return redirect(url_for('courses.index'))
        flash('Email o contraseña incorrectos', 'danger')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            AuthService.register(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data,
                password=form.password.data,
                role=form.role.data
            )
            flash('Cuenta creada con éxito. Ya podés iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
        except ValueError as e:
            flash(str(e), 'danger')
    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))