from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user,logout_user, login_required, current_user
from .models import User, Possession, Product, Required
from . import db
from sqlalchemy import and_
import MySQLdb

# from reportlab.pdfgen import canvas
# from reportlab.pdfbase import pdfmetrics
# from reportlab.pdfbase.cidfonts import UnicodeCIDFont
# from reportlab.lib.pagesizes import A4, portrait
# from reportlab.platypus import Table, TableStyle
# from reportlab.lib.units import mm
# from reportlab.lib import colors 
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# import json
# import time
# from fpdf import FPDF
# from pdfkit import pdfkit
# from response import Response
from .pdf import pdf

auth = Blueprint('auth', __name__, static_folder='static')

@auth.route('/login')
def login():
    return render_template('login.html')

@auth.route('/signup')
def signup():
    return render_template('signup.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@auth.route('/register')
@login_required
def register():
    return render_template('register.html')

@auth.route('/create')
@login_required
def create():
    return render_template('create.html')

@auth.route('/check')
@login_required
def check():
    render_template('check.html')


@auth.route('/signup', methods=['POST'])
def signup_post():
    # code to validate and add user to database goes here

    email = request.form.get('email')
    name = request.form.get('name')
    password = request.form.get('password')

    user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database

    if user: # if a user is found, we want to redirect back to signup page so user can try again
        flash('Email address already exists')
        return redirect(url_for('auth.signup'))

    # create a new user with the form data. Hash the password so the plaintext version isn't saved.
    new_user = User(email=email, name=name, password=generate_password_hash(password, method='sha256'))

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('auth.login'))

@auth.route('/login', methods=['POST'])
def login_post():
    email = request.form.get('email')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False

    user = User.query.filter_by(email=email).first()

    # check if the user actually exists
    # take the user-supplied password, hash it, and compare it to the hashed password in the database
    if not user or not check_password_hash(user.password, password):
        flash('メールアドレスかパスワードが正しくありません。')
        return redirect(url_for('auth.login')) # if the user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    # login code goes here
    login_user(user, remember=remember)
    return redirect(url_for('main.index'))

@auth.route('/register', methods=['POST'])
@login_required
def register_post():
    id = User.get_id(current_user)
    material = request.form.get('material')
    quantity =	request.form.get('quantity')

    material = Possession(id = id, material = material, quantity =quantity)
    db.session.add(material)
    db.session.commit()

    return redirect(url_for('auth.register'))

@auth.route('/create', methods = ['POST'])
@login_required
def create_post():
    id = request.form.get('radio')
    product = Product.query.filter_by(id=id).first()
    return render_template('check.html', product=product)

@auth.route('/check', methods = ['POST'])
@login_required
def check_post():
    id = request.form.get('product')
    user = User.get_id(current_user)

    conn = MySQLdb.connect(
        unix_socket = 'http://localhost/phpmyadmin/index.php?route=/sql&db=db_test&table=possession&pos=0',
        user='root',
        passwd='',
        host='localhost',
        db='db_test'
    )
    
   
    # カーソルを取得する
    cur = conn.cursor()

    # SQL（データベースを操作するコマンド）を実行する
    sql = (f"SELECT * FROM required LEFT OUTER JOIN possession ON required.material = possession.material AND possession.id = {user} WHERE possession.material IS NULL AND required.id = {id}")
    cur.execute(sql)


    # 実行結果を取得する
    data = cur.fetchall()
    for row in data:
        print(row)


    return render_template('end.html', data=data) #, data2 = data2

@auth.route('/end', methods = ['POST'])
@login_required
def end_post():
    data = request.form.get("data")
    print(data)
    return render_template("index.html"),pdf(data)

@auth.route('/process')
@login_required
def process():
    return render_template('process.html')

@auth.route('/process2')
@login_required
def process2():
    return render_template('process2.html')
    
       
