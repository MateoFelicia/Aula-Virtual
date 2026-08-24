# app/modules/auth/routes.py
from flask import render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required
from . import auth_bp
from .forms import LoginForm, RegisterForm, ResendConfirmationForm
from .services import AuthService


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = AuthService.authenticate(form.email.data, form.password.data)
        if user:
            if not user.email_confirmed:
                flash(
                    'Tenés que confirmar tu email antes de entrar. '
                    'Buscá el link en tu casilla o pedí uno nuevo abajo.',
                    'warning'
                )
                return render_template('auth/login.html', form=form)
            login_user(user)
            return redirect(url_for('courses.index'))
        flash('Email o contraseña incorrectos', 'danger')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            user = AuthService.register(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data,
                password=form.password.data,
                role=form.role.data
            )
            if AuthService.send_confirmation(user):
                flash(
                    'Cuenta creada. Te enviamos un link de confirmación a '
                    f'{user.email}. Confirmala para poder iniciar sesión.',
                    'success'
                )
            else:
                flash(
                    'Cuenta creada, pero no pudimos enviar el email. '
                    'Usá "Reenviar confirmación" desde la pantalla de login.',
                    'warning'
                )
            return redirect(url_for('auth.login'))
        except ValueError as e:
            flash(str(e), 'danger')
    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/confirm/<token>')
def confirm(token):
    user, message = AuthService.confirm_email(token)
    flash(message, 'success' if user else 'danger')
    return redirect(url_for('auth.login'))


@auth_bp.route('/resend-confirmation', methods=['GET', 'POST'])
def resend_confirmation():
    form = ResendConfirmationForm()
    if form.validate_on_submit():
        AuthService.resend_confirmation(form.email.data)
        # Mensaje igual siempre: no revelamos si el email existe o no
        flash(
            'Si el email corresponde a una cuenta sin confirmar, '
            'te enviamos un nuevo link. Revisá tu casilla.', 'info'
        )
        return redirect(url_for('auth.login'))
    return render_template('auth/resend_confirmation.html', form=form)