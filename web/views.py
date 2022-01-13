from typing import Awaitable
from web import app
from flask import json, render_template, request, session, url_for, redirect, flash, jsonify
from markupsafe import escape
from werkzeug.utils import redirect
from BD.DataBase import Login, Users, Sensores, WatterQuality
from email.utils import parseaddr
from web.forms import Cadastro, ResetPassword, NewPassword
from web.mail import SendMail
import os

from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

@app.route("/", methods=['GET'])
def index(**kwargs):
    if "user" in session:
        if session['user']['valid']==True:
            return redirect(url_for("dashboard"))
        else:
            return redirect(url_for("valida"))
    else:
        return render_template("index.html")

@app.route("/login/", methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        login = Login()
        user = request.form['user']
        passwd = request.form['password']
        
        if ('@' in parseaddr(user)[1]):
            valid = login.passwdLogin(email=user, password=passwd, ip=request.remote_addr)

            if "USER" in valid:
                ntoken = login.validAccount(valid.get("USER")[2])
                usuario= {
                    "id": valid.get("USER")[0],
                    "username": valid.get("USER")[2],
                    "nome" : valid.get("USER")[1],
                    "email" : valid.get("USER")[3],
                    "valid" : False
                }
                print(ntoken)
                if "TOKEN" in ntoken:
                    usuario['valid'] = ntoken['TOKEN'][-1]
                    
                else:
                    usuario['valid'] = False

                session['user'] = usuario
                return redirect(url_for("dashboard"))
            else:
                flash("Email/usuário ou senha inválidos")
                return redirect(url_for("index"))
        else:
            valid = login.passwdLogin(username=user, password=passwd, ip=request.remote_addr)

            if "USER" in valid:
                ntoken = login.validAccount(user)
                usuario= {
                    "id": valid.get("USER")[0],
                    "username": valid.get("USER")[2],
                    "nome" : valid.get("USER")[1],
                    "email" : valid.get("USER")[3],
                    "valid" : False
                }
                if "TOKEN" in ntoken:
                    usuario['valid'] = ntoken['TOKEN'][-1]
                    
                else:
                    usuario['valid'] = False

                session['user'] = usuario
                return redirect(url_for("dashboard"))
            else:
                flash("Email/usuário ou senha inválidos")
                return redirect(url_for("index"))

    else:
        return redirect(url_for("index"))

@app.route("/cadastro", methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        form = Cadastro(request.form)
        if form.validate_on_submit():
            users = Users()
            nome = form.nome.data.capitalize() + " " + form.sobrenome.data.capitalize()
            email = form.email.data
            senha = form.passwd.data
            username= form.username.data

            users.save(nome, username, email, senha)
            token = Login()
            ntoken = token.validAccount(username)

            user = {
                'email': email,
                'nome' : nome,
                'username':username,
                'valid' : False
            }

            if "TOKEN" in ntoken:
                user.update({"valid":ntoken['TOKEN'][-1]})
                
                if ntoken['TOKEN'][-1] == False:
                    mail = SendMail([nome, username, email])
                    mail.sendToken(ntoken["TOKEN"][1])

                session['user'] = user
            else:
                session['user'] = user
            
            return redirect(url_for("valida"))
        else:
            return render_template("cadastrar.html", form=form, action="cadastro", title="Cadastro")
    form = Cadastro()
    return render_template("cadastrar.html", form=form, action="cadastro", title="Cadastro")

@app.route("/valida", methods=['GET', 'POST'])
def valida():
    login = Login()
    if request.method == 'POST':

        token = ''
        for code in request.form:
            if "code" in code:
                token = token + request.form[code]
        

        username = session['user']['username']
        getValid = login.validToken(username, token)
        try:
            if "SUCESS" in getValid:
                session['user']['valid'] = True
                session.modified = True
                return redirect(url_for("dashboard"))
            else:
                flash(getValid['ERRO'])
                return redirect(url_for("valida"))
        except Exception as e:
            flash("Erro ao Validar Token")
            return redirect(url_for("valida"))
    else:
        if "user" in session:
            if session['user']['valid']==False:
                return render_template("validEmail.html", user=session['user'])
            else:
                return redirect(url_for("dashboard"))
        else:
            return redirect(url_for("index"))

@app.route("/reenvia")
def reenvia():
    if  "user" in session:
        if session['user']['valid']==False:
            nome = session['user']['nome']
            username = session['user']['username']
            email = session['user']['email']

            login = Login()
            mail = SendMail([nome, username, email])

            ntoken = login.newToken(username)
            if "ERRO" in ntoken:
                flash(ntoken['ERRO'])
            else:
                mail.sendToken(ntoken["TOKEN"][1])
            return redirect(url_for("valida"))
        else:
            return redirect(url_for("dashboard"))
    else:
        return redirect(url_for("index"))


@app.route("/esqueci-senha", methods=['GET', 'POST'])
def resetPassword():
    if request.method == 'POST':
        form = ResetPassword(request.form)

        if form.validate_on_submit():
            users = Users()
            if "@" in parseaddr(form.user.data)[1]:
                form = users.getUser(email=form.user.data)
            else:
                form = users.getUser(username=form.user.data)
            user = {
                "id" : form[0],
                "nome" : form[1],
                "username": form[2],
                "email" : form[3],
                "valid" : False
            }
            session['user'] = user
            session.modified = True
            return redirect(url_for("validaEmail"))
        else:
            return render_template("cadastrar.html", form=form, action="resetPassword", title="Reset-Senha")
    else:
        form = ResetPassword()
        return render_template("cadastrar.html", form=form, action="resetPassword", title="Reset-Senha")

@app.route("/nova-senha", methods=['POST', 'GET'])
def novaSenha():
    if request.method == 'POST' and "user" in session:
        form = NewPassword(request.form)
        if form.validate_on_submit():
            user = Users()
            if not "ERRO" in user.update(session['user']['username'], senha=form.passwd.data):
                user.update(session['user']['username'], senha=form.passwd.data)
                session.pop("user", None)
                return redirect(url_for("index"))
            else:
                return redirect(url_for("resetPassword"))
    elif "user" in session:
        form = NewPassword()
        return render_template("cadastrar.html", action="novaSenha", form=form, title="Reset-Senha", user=session['user'])
    else:
        return redirect(url_for("index"))

@app.route("/valida/reset", methods=['GET', 'POST'])
def validaEmail():
    if request.method == 'POST':
        token = ''
        for code in request.form:
            if "code" in code:
                token = token + request.form[code]
        login = Login()
        username = session['user']['username']
        getValid = login.validToken(username, token)
        #try:
        if "SUCESS" in getValid:
            session['user']['valid'] = False
            session.modified = True
            return redirect(url_for("novaSenha"))
        else:
            flash(getValid['ERRO'])
            return redirect(url_for("validaEmail"))
        #except Exception as e:
            #return redirect(url_for("index"))
                
    elif "user" in session:
        return render_template("validEmail.html", action="validaEmail", token="reenviaToken", title="Valida Email", user=session['user'])
    else:
        return redirect(url_for("index"))


@app.route("/reenvia-token")
def reenviaToken():
    if  "user" in session:
        if session['user']['valid']==False:
            nome = session['user']['nome']
            username = session['user']['username']
            email = session['user']['email']

            login = Login()
            mail = SendMail([nome, username, email])

            ntoken = login.newToken(username)
            if "ERRO" in ntoken:
                flash(ntoken['ERRO'])
            else:
                mail.sendToken(ntoken["TOKEN"][1])
            return redirect(url_for("validaEmail"))
        else:
            return redirect(url_for("dashboard"))
    else:
        return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop('_flashes', None)
    return redirect(url_for("index"))

@app.route("/dashboard")
async def dashboard():
    if "user" in session:
        if session['user']['valid']==True:
            return render_template("dashboard.html")
        else:
            return redirect(url_for("valida"))
    else:
        return redirect(url_for("index"))


@app.route("/temp")
async def temp():
    if "user" in session:
        data = await check_CPU_temp()
        data = {"temp": data['temp1_input']}
        return  jsonify(data)
    else:
        return redirect(url_for("index"))

@app.route("/quality")
@app.route("/quality/<reservatorio>")
async def quality(reservatorio=None):
    if 'user' in session:
        username = session['user']['username']
        sensores = WatterQuality()
        get = await sensores.getQuality(username, reservatorio)
        if 'ERROR' == get:
            return jsonify({"data": {"Not Data"}})
        else:
            return jsonify({"data":get})
    else:
        return redirect(url_for("index"))


async def check_CPU_temp():
    import re, subprocess
    import time
    data = dict()
    while True:
        err, msg = subprocess.getstatusoutput('sensors -j')
        if not err:
            m = json.loads(msg)
            for x in m:
                if "CPU" in m[x]:
                    data = m[x]
        #time.sleep(1)
        return data['CPU']