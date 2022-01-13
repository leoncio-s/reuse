from flask_wtf import FlaskForm
from wtforms import Form, StringField, PasswordField
from wtforms.fields.simple import HiddenField, SubmitField
from wtforms.validators import InputRequired, Email, Length, EqualTo, DataRequired, ValidationError
from BD.DataBase import Users, Login
from email.utils import parseaddr
#form = FlaskForm(meta={'csrf':True})

#WTF_CSRF_ENABLED = True

class Cadastro(FlaskForm):
    nome = StringField(u"Nome", [Length(min=3, max=25), InputRequired("Campo obrigatório")])
    sobrenome = StringField(u"Sobrenome", [Length(min=3, max=25), InputRequired("Campo Obrigatório")])
    email     = StringField(u"Email", [Length(min=3, max=100), InputRequired(), Email("Entre com um endereço de e-mail Válido")])
    username = StringField(u"Nome de Usuário", [Length(min=3, max=20), InputRequired("Campo Obrigatório")])
    passwd = PasswordField(u"Senha", [Length(min=3, max=200), DataRequired(), EqualTo("confirmpassword", message="Senhas devem coincidir")])
    confirmpassword = PasswordField(u"Confirme a Senha", [InputRequired("Este campo é óbrigatório")])

    def validate_username(self, username):
        users = Users()
        user = users.getUser(username=username.data)
        if user != 0:
            raise ValidationError('Nome de usuário inválido')
        else:
            pass
    
    def validate_email(self, email):
        users = Users()
        user = users.getUser(email=email.data)
        if user != 0:
            raise ValidationError('Email já cadastrado')
        else:
            pass

class ResetPassword(FlaskForm):
    user = StringField(u"Nome de Usuário ou Email", [Length(min=3, max=100), InputRequired("Campo Obrigatório")])
    def validate_user(self, user):
        users = Users()
        username = user.data
        if '@' in parseaddr(username)[1]:
            currentUser = users.getUser(email=username)

            if user == 0:
                raise ValidationError("Usário Inválido")
            else:
                login = Login()
                if "ERRO" in login.resetPassword(currentUser[2]):
                    raise ValidationError("Erro Inesperado")
                else:
                    login.resetPassword(currentUser[2])

        else:
            currentUser = users.getUser(username=username)

            if user == 0:
                raise ValidationError("Usário Inválido")
            else:
                login = Login()
                if "ERRO" in login.resetPassword(currentUser[2]):
                    raise ValidationError("Erro Inesperado")
                else:
                    login.resetPassword(currentUser[2])


class NewPassword(FlaskForm):
    passwd = PasswordField(u"Senha", [Length(min=3, max=200), DataRequired(), EqualTo("confirmpassword", message="Senhas devem coincidir")])
    confirmpassword = PasswordField(u"Confirme a Senha", [InputRequired("Este campo é óbrigatório")])