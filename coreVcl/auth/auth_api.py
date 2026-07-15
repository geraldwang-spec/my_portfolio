from flask import Blueprint, render_template

def create_auth_bp()->Blueprint:
    auth_bp = Blueprint('auth', __name__, url_prefix="/auth")
    
    @auth_bp.route('/login')
    def login()->str:
        return render_template("login.html")

    @auth_bp.route('/resetpasswd')
    def reset_passwd_html():
        return render_template('reset_passwd.html')

    return auth_bp
