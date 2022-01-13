from asyncio.tasks import wait
from typing import AsyncIterator
from BD import sq
import re, os, hashlib, datetime, json
from binascii import unhexlify
import random
import asyncio
#from psycopg.sql import NULL


BASE_DIR=os.path.dirname(os.path.dirname(__file__))
global conn
global c

class DataBase:
    def __init__(self):
        try:
            conn, c
        except:
            conn, c = self.connect()

    def connect(self):
        #try:
        global conn
        global c

        try:
            return conn, conn.cursor()
        except:
            if os.path.exists( BASE_DIR + "/.env.json"):
                with open(os.path.dirname(os.path.dirname(__file__)) + "/.env.json") as db:
                    self.js = json.load(db)

                    self.db = {
                        "host" : self.js["BD_HOST"],
                        "user" : self.js["BD_USER"],
                        "port" : self.js["BD_PORT"],
                        "password" : self.js["BD_PASWD"],
                        "dbname" : self.js["BD_BASE"]
                    }
                    try:
                        conn = sq.connect(f"host={self.db['host']}, user={self.db['user']}, port={self.db['port']}, password={self.db['password']}, dbname={self.db['dbname']}")
                    except sq.Error:
                        conn = sq.connect(self.js["BD_URI"])
                    except Exception as e:
                        return {'error': e}

                    c = conn.cursor()
                    dirname = os.path.dirname(__file__)
                    sql = open(dirname + "/agua_reuso.sql", "r+").read()
                    print("Database version: ", c.execute("SELECT version();").fetchone())
                
                    c.execute(sql)

                    conn.commit()
                    print ("Sucessfull connection")
                    return conn, conn.cursor()
            else:
                print("ARQUIVO .env.json NÃO LOCALIZADO")
                return exit()
                       
            
            #except Exception  as e:
            #    return {'error': e}
    
    def close(self):
        global conn, c
        return conn.close()

class Sensores(DataBase):

        # Retorna os sensores ativos por usuários
        async def ativos(self, usuario):
            self.user = str(re.sub('[^a-z0-9]+', '', usuario.lower()))

            try:
                self.logS = LogsSensores()
                self.data = await self.logS.selectUser(self.user)
                self.sensores = []
                if (self.data != 0):
                    for x in self.data:
                        self.sensores.append(await c.execute(f"""
                            SELECT * FROM reuse.sensores
                            WHERE id={x[3]} and
                            deleted <> True
                            """).fetchone())
                    return self.sensores
                else:
        
                    return ["Invalid Query"]
            except Exception as e:
                return e
            
        # insere nova linha na tabela sensores
        def save(self, name, s_type, pin, user, **kwargs):
            self.insert = 0
            self.name       = re.sub('[^A-Za-z0-9]+', '', name)
            self.type          = re.sub('[{1}^A-Z]+', '', s_type)
            self.pin            = int(pin)
            self.user          =  re.sub('[^A-Za-z0-9]+', '', user.lower())
            self.data    = datetime.datetime.now(datetime.timezone.utc)

            if (self.name == None or self.type == None or self.pin ==None or self.user == None):
                return "Invalid Values"
            else:
                try:
                    c.execute("INSERT INTO reuse.sensores(nome, tipo, pino, usuario) VALUES(%s, %s, %s, %s, %s)", (self.name, self.type, self.pin, self.user))
                    conn.commit()
                    self.insert = 1

                except Exception as e:
                    print(e)

                try:
                    if self.insert == 1:

                        self.id = c.execute(f"""
                            SELECT id FROM reuse.sensores
                            WHERE nome = '{self.name}' and
                            tipo = '{self.type}' and
                            pino = {self.pin}
                        """).fetchone()

                        self.users = Users()

                        self.usuario = self.users.getUser(self.user)

                        if(len(self.usuario) == 0 or self.usuario==""):
                            return "Usuário não existe ou não foi encontrado"
                        else:
                            self.logs_sensores = LogsSensores()
                            self.logs_sensores.save(self.usuario[2], self.id[0])
                    else:
                        return "Não foi possível completar a solicitação"

                except Exception as e:
                    conn.close()
                    return e

        # Retorna os sensores cadastrados, filtrando por nome, pino, tipo ou id, na falta desses, retorna todos os sensores cadastrados
        def select(self, name=None, pin=None, s_type=None, id=None):
            self.name   = re.sub("[A-Za-z0-9]+", '', name) if name!= None else None
            self.pin        = int(pin) if pin != None else None
            self.type      = re.sub('[{1}^A-Z]+', '', s_type) if ((s_type != None) and (len(s_type)==1)) else None
            self.pin        = int(pin) if id != None else None
            self.query   = "SELECT * FROM reuse.sensores WHERE "

            if (self.name and self.pin and self.type and self.id) == None:
                self.query = "SELECT * FROM reuse.sensores WHERE deleted != 'True'"
            elif self.id != None:
                    self.query = self.query + f"id = {self.id} and deleted != 'True'"
            elif(self.name  and self.pin and self.type) != None:
                self.query = self.query + f"""
                        nome = '{self.name}' and
                        pino = {self.pin} and
                        tipo = '{self.type} and
                        deleted <> True
                """
            elif (self.name and self.pin) != None:
                self.query = f"{self.query} nome='{self.name}' and pino={ self.pin} and deleted != 'True'"
            elif (self.name and self.type) != None:
                self.query = self.query + f"nome={self.name} and tipo='{self.type}' and deleted != 'True'"
            else:
                return 0
            
            try:
                self.data = c.execute(self.query).fetchall()
                if self.data == None or len(self.data) == 0:
                    return 0
                else:
                    return self.data
            except Exception as e:
                return e

        # Atualiza os dados dos sensores
        def update(self, id:int, user:str, values:dict, **kwargs):
            self.id         = id
            self.user       = re.sub("[^a-z0-9]", '', user.lower())
            self.values     = values
            self.updated    = datetime.datetime.now(datetime.timezone.utc)
            self.ip         = kwargs.get("ip")

            for x in self.values.keys():
                if x.lower() == 'nome':
                    self.values[x] = re.sub("[^A-Za-z0-9]", "", self.values[x])
                elif  x.lower() == 'pino':
                    self.values[x] = int(self.values[x])
                elif x.lower() == 'tipo':
                    self.values[x] = re.sub("[^A-Za-z0-9]", "", self.values[x])
                else:
                    print("INVALID COLLUMN")
                    return "INVALID COLLUMN"

            self.new = re.sub("[^A-Za-z0-9: ,]", "", str(self.values))
            self.new = self.new.replace(": ", "='")
            self.new = self.new.replace(",", "',")
            self.new = self.new + "'"

            self.users = Users()
            self.usuario = self.users.getUser(self.user)


            if(self.usuario == 0):
                return "Usuário não existe ou não foi encontrado"

            try:
                c.execute(f"""
                        UPDATE reuse.sensores
                        SET {self.new}, updated='{self.updated}'
                        WHERE id={self.id}
                        """)
                conn.commit()

                self.logS = LogsSensores()

                self.logS.save(self.usuario[2], self.id, self.ip)
                
                return "SUCESSFUL UPDATED"

            except Exception as e:
                conn.close()
                return e

        def delete(self, id:int, user:str, ip=None):
            self.id = id
            self.user = re.sub("[^a-z0-9]","", user.lower())
            self.ip         = re.sub('[^0-9.]+', '', ip) if ip != None else None
            self.data = datetime.datetime.now(datetime.timezone.utc)
    
            try:
                self.usuarios = Users()
                if self.usuarios.getUser(self.user) == 0:
                    return ValueError("Usuário inválido ou inexistente")
                else:
                    c.execute("UPDATE reuse.sensores SET deleted='True' WHERE id=%s and updated='%s'", (self.id, self.data))
                    self.logs = LogsSensores()
                    self.logs.save(self.user, self.id, self.ip)
                    return "SUCESSFULL UPDATE"
            except Exception as e:
                return e

class Users(DataBase):
    # Salva um novo usuário e senha
    def save(self, name:str, username:str, email:str, passwd:str):
        self.name = re.sub("\[^A-Za-z ]", '', name.capitalize())
        self.username = re.sub("[^a-z0-9]", "", username.lower())
        self.email = re.sub("[^a-z0-9@.-_]+", "", email.lower())
        self.password = self.setPassword(passwd, self.username)
        self.date = datetime.datetime.now(datetime.timezone.utc)
        print(self.username)
        try:
            c.execute(f"""
                        INSERT INTO reuse.usuarios(nome, username, senha, email)
                        VALUES ('{self.name}', '{self.username}', '{self.password}', '{self.email}')
                    """)
            
            if c.statusmessage != "INSERT 0":
                conn.commit()
                return c.statusmessage
            else:
                raise ValueError("Invalid Fields")
        except Exception as e:
            return e
    # criptografa a senha
    def setPassword(self, password:str, user:str):
        self.password = password
        self.user   = user

        self.passtoencrypt = self.password

        self.salt = os.urandom(len(user))
        self.key  = hashlib.pbkdf2_hmac("sha256", self.passtoencrypt.encode("utf-8"), self.salt, 100000)

        self.criptPassword = f"PBKDF2_HMAC${self.key.hex()}${self.salt.hex()}"

        #print(self.criptPassword.decode("latin-1").encode("utf-8"))
        return self.criptPassword
    # puxa a senha criptografada e atribui verifica se é igual a senha atual
    def getPassword(self, password:str, user:str):
        self.passwd = password
        self.user   = re.sub("[^a-z0-9]", "", user.lower())

        try:
            self.password = c.execute(f"SELECT senha, senha_old FROM reuse.usuarios WHERE username='{self.user}'").fetchone()
            
            self.salt = self.password[0].split("$")[-1] if self.password[0] != None else None
            self.key  = self.password[0].split("$")[1] if self.password[0] != None else None
            self.salt_old = self.password[1].split("$")[-1] if self.password[1] != None else None
            self.key_old  = self.password[1].split("$")[1] if self.password[1] != None else None

            if self.key_old != None: 
                self.new_old_key = hashlib.pbkdf2_hmac("sha256", self.passwd.encode("utf-8"), unhexlify(self.salt_old), 100000).hex()
            else:
                self.new_old_key = None

            self.new_key = hashlib.pbkdf2_hmac("sha256", self.passwd.encode("utf-8"), unhexlify(self.salt), 100000).hex()
            
            if self.new_key == self.key and self.key != None:
                return 1
            elif self.new_old_key == self.key_old and self.key_old != None:
                return 2
            else:
                return 0
        except Exception as e:
            return e

    # Puxa o usuário ativo
    def getUser(self, username=None, email=None):
        self.user = re.sub("[^a-z0-9]", '', username.lower()) if username != None else None
        self.email = re.sub("[^a-z0-9@.-_]+", "", email.lower()) if email != None else None

        try:
            if self.user != None:
                self.usuario = c.execute(f"SELECT id, nome, username, email, created FROM reuse.usuarios WHERE username='{self.user}' and deleted != 'True'").fetchone()
                if self.usuario==None or len(self.usuario) == 0:
                    return 0 #ValueError("Usuário invalido ou inexistente")
                else:
                    return self.usuario
            elif self.email != None:
                self.usuario = c.execute(f"SELECT id, nome, username, email, created FROM reuse.usuarios WHERE email='{self.email}' and deleted != 'True'").fetchone()
                if self.usuario==None or len(self.usuario) == 0:
                    return 0 #ValueError("Usuário invalido ou inexistente")
                else:
                    return self.usuario
            else:
                raise ValueError({"ERROR": "INVALID FIELDS"})
        except Exception as e:
            raise ValueError(e)
    # Atualiza o usuário
    def update(self, user:str, **kwargs):
        self.user = re.sub("[^a-z0-9]", "", user.lower())
        self.query = []
        self.data = datetime.datetime.now(datetime.timezone.utc)
        self.getSenha = 1

        #print(kwargs)

        try:
            for field in kwargs.keys():
                #print(field)
                if field == 'nome':
                    self.query.append(f"nome='{kwargs.get(field)}'")
                elif field == 'senha':
                    self.getSenha = self.getPassword(kwargs.get(field), self.user)
                    if self.getSenha == 0:
                        self.senha = self.setPassword(kwargs.get(field), self.user)
                        self.senha_old = c.execute(f"SELECT senha FROM reuse.usuarios WHERE username='{self.user}'").fetchone()[0]

                    elif self.getSenha == 1:
                        return {"ERROS1": "Senha já cadastrada"}
                    else:
                        return {"ERROS1": "Senha antiga"}
                    
                elif field == 'username':
                    self.query.append(f"username='" + re.sub("[^a-z0-9]", "", str(kwargs.get(field)).lower()) + "'")
                elif field == 'email':
                    self.query.append(f"email='" + re.sub("[^a-z0-9@.-_]+", "", str(kwargs.get(field)).lower()) + "'")
                else:
                    print(f"Campo {field} invalido")

            self.query = str(self.query).replace('["', "")
            self.query = self.query.replace('"]', "")
            self.query = self.query.replace('"', "")

            if 'senha' in kwargs and self.query != '[]':
                c.execute(f"UPDATE reuse.usuarios SET {self.query}, senha='{self.senha}', senha_old='{self.senha_old}' WHERE username='{self.user}'")
            elif('senha' in kwargs and self.query == '[]' and self.getSenha==0):
                c.execute(f"UPDATE reuse.usuarios SET senha='{self.senha}', senha_old='{self.senha_old}' WHERE username='{self.user}'")
            elif(self.getSenha != 1 and self.query == '[]'):
                return ValueError("NOTHING TO COMMIT")
            else:
                c.execute(f"UPDATE reuse.usuarios SET {self.query} WHERE username='{self.user}'")

            if c.statusmessage != "UPDATE 0":
                conn.commit()
                return {"SUCESS": c.statusmessage}
            else:
                conn.rollback()
                return {"ERRO":"UPDATE FAILURE"}
        except Exception as e:
            return e
            
    def delete(self, user:str):
        self.user = re.sub("[^a-z0-9]", "", user.lower())
        self.data         = datetime.datetime.now(datetime.timezone.utc)
        try:
            self.usuario = c.execute(f"SELECT id, nome, username, email FROM reuse.usuarios WHERE username='{self.user}'")
            if len(self.usuario) == 0:
                return ValueError("USUÁRIO INVALIDO OU INEXISTENTE")
            else:
                c.execute(f"UPDATE reuse.usuarios SET deleted='True', updated='{self.data}'")
                conn.commit()
                return c.statusmessage
        except Exception as e:
            return e

class Reservatorio(DataBase):
    # Salva um novo reservatório
    def save(self, nome:str, tipo:str, capacidade:float):
        self.name = re.sub("[^A-Za-z0-9 ]+", "", nome)
        self.type = re.sub('[^A-Za-z0-9]+', '', tipo)
        self.cap  = capacidade
        self.data = datetime.datetime.now(datetime.timezone.utc)

        try:
            c.execute(f"INSERT INTO reuse.reservatorio(nome, tipo, capacidade, created, updated) VALUES('{self.name}', '{self.type}', {self.cap}, '{self.data}', '{self.data}')")
            conn.commit()
            return c.statusmessage
        except Exception as e:
            return e

    # Retorna os dados dos resevatórios por id ou capacidade e nome
    def select(self, id:int, **kwargs):
        self.id = id
        self.nome = kwargs.get("nome") if ('nome' in kwargs) else None
        self.capacidade = float(kwargs.get("capacidade")) if ('id' in kwargs) else None

        try:
            if self.id == None and ("nome", "capacidade", "tipo") not in kwargs:
                return ValueError("Invalid fields")
            elif(self.id != None or self.id != NULL):
                self.data = c.execute(f"SELECT * FROM reuse.reservatorio WHERE id={self.id}")
                return self.data
            elif(self.id == None and (self.nome, self.capacidade) != None):
                self.data = c.execute(f"SELECT * FROM reuse.reservatorio WHERE nome={self.nome} and capacidade={self.capacidade}")
                return self.data
            else:
                return ValueError("Invalid Fields")
        except Exception as e:
            return e

    #Atualiza dados da tabela reservatorio
    def update(self, id:int, **kwargs):
        self.id = id
        self.data = datetime.datetime.now(datetime.timezone.utc)
        print(kwargs)
        if ("nome" in kwargs) or ("tipo" in kwargs) or ("capacidade" in kwargs):
            self.query = [f"{x}='{kwargs.get(x)}'" for x in kwargs.keys()]
        else:
            return ValueError("Invalid Fields")
        try:
            self.query = str(self.query).replace('["', "")
            self.query = self.query.replace('"]', "")
            self.query = self.query.replace('"', "")

            c.execute(f"UPDATE reuse.reservatorio SET {self.query}, updated='{self.data}' WHERE id={self.id}")

            conn.commit()
            if c.statusmessage != 'UPDATE 0':
                return c.statusmessage
            else:
                return ValueError("Invalid values") 
        except Exception as e:
            return e

class LogsSensores(DataBase):

    def save(self, usuario:str, sensor:int, ip=None):
        self.usuario    = re.sub('[^a-z0-9]+', '', usuario.lower())
        self.sensor     = sensor
        self.ip         = re.sub('[^0-9.]+', '', ip) if ip != None else None
        self.data       = datetime.datetime.now(datetime.timezone.utc)

        try:
            c.execute('''
                INSERT INTO reuse.logs_sensores(usuario, ip, sensor, datahora)
                VALUES(%s, %s, %s, %s)''', (self.usuario, self.ip, self.sensor, self.data))
            
            conn.commit()

            return "Sucessfull"
        except Exception as e:
            return e

    async def selectUser(self, user:str):
        self.user    = re.sub('[^a-z0-9]+', '', user.lower())

        try:
            self.data = c.execute('''
                SELECT * FROM reuse.logs_sensores L WHERE L.usuario = '%s'
            ''', (self.user)).fetchall()

            if (self.data != None or len(self.data) != 0):
                return self.data
            else:
                return 0
        except Exception as e:
            conn.close()
            return e

    def selectSensor(self, sensor:int):
        self.sensor    = sensor

        try:
            self.data = c.execute('''
                SELECT * FROM reuse.logs_sensores L WHERE L.sensor = %s
            ''', (self.sensor)).fetchall()

            if (self.data != None  or len(self.data) != 0):
                return self.data
            else:
                return 0
        except Exception as e:
            conn.close()
            return e

class LogsReservatorios(DataBase):
    def save(self, reserv:int, user:str, **kwargs):
        self.reserv = reserv
        self.user   = user
        self.ip  = kwargs.get("ip") if 'ip' in kwargs.keys() else NULL

        try:
            if self.user != None and self.reserv != None:
                c.execute(f"INSERT INTO reuse.logs_reservatorio(usuario, ip, reserv, datahora) VALUES('{self.usuario}', '{self.ip}', {self.reserv}, now())")

                if c.statusmessage != "INSERT 0":
                    conn.commit()
                    return c.statusmessage
            else:
                return ValueError("Invalid Fields")
        except Exception as e:
            print (e)

class ActiveSensor(DataBase):

    def save(self, sensor:int, status:str):
        self.sensor = sensor
        self.status = re.sub('[^{1}AFI]', '', status.upper())
        self.data   = datetime.datetime.now(datetime.timezone.utc)

        self.sensores = Sensores()
        self.id_sensor = self.sensores.data(id=self.sensor)

        try: 
            if ((len(self.status) != 1 and self.status not in ('A', 'F', 'I')) or self.id_sensor == 0 ):
                return ["Invalid Query"]
            else:
                c.execute("""
                    INSERT INTO reuse.active_sensor(sensor, status, created, updates)
                    VALUES(%s, %s, %s, %s)
                """, (self.sensor, self.status, self.data, self.data))

                conn.commit()

            return "Sucessfull!"
        except Exception as e:
            conn.close()
            return e

    def select(self, sensor:int):
        self.sensor = sensor

        try: 
            self.data = c.execute(
                f""" SELECT * FROM reuse.active_sensor WHERE sensor={self.sensor} ORDER BY UPDATED ASC """
                ).fetchone()
        
            if len(self.data) == 0:
                return 0
            else:
                return self.data
        except Exception as e:
            conn.close()
            return e

    def update(self, sensor:int, status:str):
        self.sensor = sensor
        self.status = re.sub('[^{1}AFI]', '', status.upper())
        self.data         = datetime.datetime.now(datetime.timezone.utc)
        try:
            c.execute(f"UPDATE reuse.active_sensor SET status='{self.status}', updated='{self.data} WHERE sensor={self.sensor}")

            return "SUCESSFULL UPDATED"
        except Exception as e:
            return e

class FluxoAgua(DataBase):
    def save(sensor:int, litros:float):
        self.sensor = sensor
        self.litros = litros
        self.data = datetime.datetime.now(datetime.timezone.utc)

        try:
            self.sensores = Sensores()
            if self.sensores.data(id=self.sensor) == 0:
                return ValueError("SENSOR INVALIDO OU INATIVO")
            else:
                c.execute("INSERT INTO reuse.fluxo_agua(sensor, litros, created, updated) VALUES(%s, %s, '%s', '%s')", (self.sensor, self.litros, self.data, self.data))
                conn.commit()

                return "SUCESSFULL CREATE"
        except Exception as e:
            return e
    
    def select(self, sensor:int):
        self.sensor = sensor

        try:
            self.data = c.execute("SELECT * FROM reuse.fluxo_agua WHERE sensor=%s", (self.sensor)).fetchall()

            if len(self.data) == 0:
                return 0
            else:
                return self.data
        except Exception as e:
            return e

class WatterMeter(DataBase):
    # Cria nova linha na tabela agua_ph
    def save(self, sensor:int, reservatorio:int, valor:float):
        self.sensor = sensor
        self.reserv = reservatorio
        self.value = round(valor, 2)

        try:
            c.execute(f"INSERT INTO reuse.agua_ph(sensor, reserv, valor, created, updated) VALUES({self.sensor},{self.reserv},{self.value},now(),now())")
            if c.statusmessage != 'INSERT 0':
                conn.commit()
                return c.statusmessage
            else:
                return ValueError("Invalid fields")
        except Exception as e:
            return e

    def select(self, **kwargs):

        if ("id" in kwargs.keys()) or ("sensor" in kwargs.keys()) or ("reserv" in kwargs.keys()):
            self.data = []
            for x in kwargs.keys():
                if x == 'sensor' or x=="reserv" or x == "id":
                    self.data.append(f"{x}={int(kwargs.get(x))}")
                else:
                    self.data.append(f"{x}='{kwargs.get(x)}'")

            x=1
            if len(self.data) > 1:
                self.query = self.data[0]

                while x < len(self.data):
                    self.query += f" and {self.data[x]}"
                    x += 1
            else:
                self.query = self.data[0]
        
        else:    return ValueError("Invalid Fields")
        
        try:
            self.query = str(self.query).replace('["', "")
            self.query = self.query.replace('"', "")
            self.query = self.query.replace('"]', "")

            self.values = c.execute(f"SELECT * FROM reuse.agua_ph WHERE {self.query}").fetchall()

            return self.values if len(self.values) != 0 else 0

        except Exception as e:
            return e

class WatterQuantity(DataBase):

    def save(self, sensor:int, reserv:int, valor:float):
        self.sensor = sensor
        self.reserv = reserv
        self.value = valor

        try:
            c.execute(f"INSERT INTO reuse.agua_quantity(sensor, reserv, valor, created, updated) VALUES({self.sensor}, {self.reserv}, {self.value}, now(), now())")
            
            if c.statusmessage != "INSERT 0":
                conn.commit()
                return c.statusmessage
            else:
                return ValueError("Invalid Fields")

        except Exception as e:
            return e

    def select(self, **kwargs):

        if ("id" in kwargs.keys()) or ("sensor" in kwargs.keys()) or ("reserv" in kwargs.keys()):
            self.data = []
            for x in kwargs.keys():
                if x == 'sensor' or x=="reserv" or x == "id":
                    self.data.append(f"{x}={int(kwargs.get(x))}")
                else:
                    self.data.append(f"{x}='{kwargs.get(x)}'")

            x=1
            if len(self.data) > 1:
                self.query = self.data[0]

                while x < len(self.data):
                    self.query += f" and {self.data[x]}"
                    x += 1
            else:
                self.query = self.data[0]
        
        else:    return ValueError("Invalid Fields")
        
        try:
            self.query = str(self.query).replace('["', "")
            self.query = self.query.replace('"', "")
            self.query = self.query.replace('"]', "")

            self.values = c.execute(f"SELECT * FROM reuse.agua_quantity WHERE {self.query}").fetchall()

            return self.values if len(self.values) != 0 else 0

        except Exception as e:
            return e

class AccessToken(DataBase):

    def save(self, username:str):
        self.user = Users()

        self.data = self.user.getUser(username)

        if self.data == 0:
            return ValueError("Invalid User")
        else:
            try:
                #print(self.data)
                self.salt = os.urandom(len(self.data[2])).hex()
                self.token = hashlib.md5(self.salt.encode("utf-8"))
                self.token.hexdigest()

                c.execute(f"INSERT INTO reuse.access_token(token, usuario) VALUES('{self.token.hexdigest()}','{self.data[2]}')")

                if c.statusmessage != "INSERT 0":
                    conn.commit()
                    return c.execute(f"SELECT usuario, expira FROM reuse.access_token WHERE token='{self.token.hexdigest()}'").fetchone()
                else:
                    conn.rollback()
                    return ValueError("Invalid fields")
            except Exception as e:
                return e

    def update(self, user:str):
        self.username= re.sub("[^a-z0-9]+", user.lower())
        self.user = Users()

        self.data = self.user.getUser(self.username)

        if self.data == 0:
            return ValueError("Invalid User")
        else:
            try:
                #print(self.data)
                self.salt = os.urandom(len(self.data[2])).hex()
                self.token = hashlib.md5(self.salt.encode("utf-8"))

                c.execute(f"UPDATE reuse.access_token SET token='{self.token.hexdigest()}', expira=(now() + interval '30 days') WHERE usuario='{self.data[2]}'")

                if c.statusmessage != "INSERT 0":
                    conn.commit()
                    return c.statusmessage
                else:
                    conn.rollback()
                    return ValueError("Invalid fields")                
            
            except Exception as e:
                return e

    def getToken(self, token:str):
        self.token=re.sub("\W\D", '', token.lower())
        
        try:
            self.data = c.execute(f"""SELECT usuario, expira, (expira - current_date) as "Restam" FROM reuse.access_token WHERE token='{self.token}'""").fetchone()
            if self.data != None:
                if self.data[2] <= 0:
                    return {'WARNING': "TOKEN HAS EXPIRED", "USER": self.data}
                else:
                    self.user = Users()
                    self.getUser = self.user.getUser(self.data[0])
                    return {"USER": self.getUser}

            else:    return {'ERRO':"INVALID TOKEN"}
        except Exception as e:
            return e
        #return 0

    def getUserToken(self, username):
        self.username=re.sub("\W\D", '', username.lower())
        
        try:
            self.user = Users()
            self.getUser = self.user.getUser(self.username)
            if self.getUser == 0:
                return {"ERROR": "INVALID USERNAME"}
            else:
                self.data = c.execute(f"""SELECT token, expira, (expira - current_date) as "Restam" FROM reuse.access_token WHERE usuario='{self.getUser[2]}'""").fetchone()
                if self.data != None:
                    if self.data[2] <= 0:
                        return {'WARNING': "TOKEN HAS EXPIRED", 'DATA': self.data}
                    else:
                        
                        return {'USER': self.getUser, 'TOKEN': self.data}

                else:    return ValueError({'ERRO':"INVALID USER OR USER HAS NOT TOKEN"})
        except Exception as e:
            return e

class LogsAcessos(DataBase):
    def save(self, usuario:str, ip:str, text=None):
        self.username = re.sub("[^a-z0-9]", "", usuario.lower())
        self.ip       = re.sub('[^0-9.]+', '', ip) if ip != None else None
        self.logs     = '' if text == None else text
        try:
            self.user = Users()
            self.getUser = self.user.getUser(self.username)

            if self.getUser == 0:
                return {"ERROR": "INVALID USER"}
            else:
                c.execute(f"INSERT INTO reuse.logs_acessos(usuario, ip, logs) VALUES ('{self.getUser[2]}', '{self.ip}', '{self.logs}')")

                if c.statusmessage != "INSERT 0":
                    conn.commit()
                    return c.statusmessage
                else:
                    conn.rollback()
                    return ValueError("Invalid fields")
        except Exception as e:
            return e

class Login(DataBase):
    
    def passwdLogin(self, password:str, username=None, email=None, **kwargs):
        self.password = password
        self.username = re.sub("[^a-z0-9]", "", username.lower()) if username != None else None
        self.email = re.sub("[^a-z0-9@.-_]+", "", email.lower()) if email != None else None

        try:
            self.user = Users()

            if(self.username == None and self.email != None):
                self.username = self.user.getUser(email=self.email)
                if self.username == 0:
                    return {"ERROR": "INVALID OR INEXISTS FIELDS"}
                else:
                    pass
            elif self.username != None:
                self.username = self.user.getUser(username=self.username)
                if self.username == 0:
                    return {"ERROR": "INVALID OR INEXISTS FIELDS"}
                else:
                    pass
            else:
                return ValueError({"ERROR": "INVALID FIELDS"})
            
            self.password = self.user.getPassword(self.password, self.username[2])

            if self.password == 1:
                self.log = LogsAcessos()
                self.log.save(self.username[2], kwargs.get("ip") if "ip" in kwargs else None, text='SUCESSFULL LOGIN WITH PASSWORD')
                return {"USER": self.username}
            elif self.password == 2:
                self.log = LogsAcessos()
                self.log.save(self.username[2], kwargs.get("ip") if "ip" in kwargs else None, text='OLD PASSWORD')
                return {"WARNING":"OLD PASSWORD"}
            else:
                self.log = LogsAcessos()
                self.log.save(self.username[2], kwargs.get("ip") if "ip" in kwargs else None, text='INVALID PASSWORD OR USERNAME/EMAIL')
                return {"ERROR":"USERNAME/EMAIL OR PASSWORD INVALID"}

        except Exception as e:
            return e
    
    def tokenLogin(self, token:str, **kwargs):
        self.token    = re.sub("[^a-z0-9]", "", token.lower())
        self.ip = kwargs.get("ip") if "ip" in kwargs else None
        try:
            self.access_token = AccessToken()
            self.data = self.access_token.getToken(self.token)

            if (not(self.data.get("WARNING"))) and (not(self.data.get("ERRO"))):
                self.log = LogsAcessos()
                self.log.save(self.data.get("USER")[2], self.ip, "SUCESSFULL LOGIN WITH TOKEN")
                return  self.data
            
            elif "WARNING" in self.data.keys():
                self.log = LogsAcessos()
                self.log.save(self.data.get("USER")[0], self.ip, text=self.data.get("WARNING"))
                return ValueError(self.data.get("WARNING"))
            
            else:
                return ValueError("INVALID TOKEN")
        except Exception as e:
            return e
    
    def validAccount(self, username:str):
        
        self.username    = re.sub("[^a-z0-9]", "", username.lower())

        try:
            users = Users()
            self.currentUser = users.getUser(self.username)

            if self.currentUser == 0:
                return {"   ": "INVALID USER"}
            else:

                self.query = f"SELECT * FROM reuse.reset_senha WHERE usuario='{self.username}' ORDER BY created DESC"
                self.data = c.execute(self.query).fetchone()

                if self.data == None or len(self.data) == 0:
                    self.token = self.newToken(self.username)
                    return self.token
                elif round((self.data[2] - datetime.datetime.now(datetime.timezone.utc)).total_seconds()/60, 2) < 0.00 and self.data[4] == False:
                    self.token = self.updateToken(self.username)
                    return self.token
                else:
                    return {"USER": self.currentUser, "TOKEN": self.data}

        except Exception as e:
            raise ValueError(e)

    def newToken(self, username:str):
        self.username = re.sub("[^a-z0-9]", "", username.lower())
        
        try: 
            self.user = Users()
            self.currentUser = self.user.getUser(self.username)
            
            if self.currentUser == 0:
                return {"ERRO": "INVALID USER"}
            else:
                self.token = ''
                for x in range(0,6):
                    self.token += str(random.randint(0,9))
                
                c.execute(f"INSERT INTO reuse.reset_senha(token, usuario) VALUES('{self.token}', '{self.username}')")
                
                if c.statusmessage != 'INSERT 0':
                    conn.commit()
                    self.query = f"SELECT * FROM reuse.reset_senha WHERE usuario='{self.username}' ORDER BY created DESC"
                    self.data = c.execute(self.query).fetchone()
                    return {"USER": self.currentUser, "TOKEN": self.data}
                else:
                    return {"ERRO":"NÃO FOI POSSÍVEL GERAR O TOKEN"}
      
        except Exception as e:
            raise ValueError(e)

    def updateToken(self, username:str):
        self.username = re.sub("[^a-z0-9]", "", username.lower())

        try: 
            self.user = Users()
            self.currentUser = self.user.getUser(self.username)
            if self.currentUser == 0:
                return {"ERROR": "INVALID USER"}
            else:
                self.token = ''
                for x in range(0,6):
                    self.token += str(random.randint(0,9))
            
                c.execute(f"UPDATE reuse.reset_senha SET used='False', token='{self.token}', expira='(now()+ interval '15 MINUTE')' WHERE usuario='{self.username}'")
        
                if c.statusmessage != 'INSERT 0':
                    conn.commit()
                    self.query = f"SELECT * FROM reuse.reset_senha WHERE usuario='{self.username}' ORDER BY created DESC"
                    self.data = c.execute(self.query).fetchone()
                    return {"USER": self.currentUser, "TOKEN": self.data}
        except Exception as e:
            raise ValueError(e)

    def validToken(self, username:str, token:str):
        self.username = re.sub("[^a-z0-9]", "", username.lower())
        self.ntoken    = re.sub("[^0-9]{6}", "", token)

        try:
           
            self.token = c.execute(f"""SELECT * FROM reuse.reset_senha WHERE usuario='{self.username}' and token='{self.ntoken}' ORDER BY created DESC""" ).fetchone()
            
            if self.token == None or len(self.token) == 0:
                return {"ERRO": "TOKEN INVÁLIDO"}
            else:
                if round((self.token[2] - datetime.datetime.now(datetime.timezone.utc)).total_seconds()/60, 2) < 0.00:
                    return {"ERRO": "O TOKEN EXPIROU, GERE UM NOVO TOKEN"}
                elif(self.token[0] == True):
                    return {"ERRO": "TOKEN INVÀLIDO"}
                else:
                    c.execute(f"UPDATE reuse.reset_senha SET used=True WHERE usuario='{self.username}'")
                    
                    if c.statusmessage != "UPDATE 0":
                        conn.commit()
                        return {"SUCESS": "TOKEN VÁLIDO"}
                    else:
                        return {"ERRO": "NÃO FOI POSSÍVEL VALIDAR O TOKEN"}

        except Exception as e:
            raise ValueError(e)

    
    def resetPassword(self, username:str):
        self.username = re.sub("[^a-z0-9]", "", username.lower())

        self.users = Users()
        try:
            self.currentUser = self.users.getUser(self.username)
            if self.currentUser == 0:
                return {"ERROR":"INVALID USER"}
            else:
                self.newToken(self.username)
                return self.users.update(self.username, senha=" ")

        except Exception as e:
            raise ValueError(e)

class WatterQuality(DataBase):

    async def getQuality(self, username:str, reservatorio=None):
        self.username = re.sub("[^a-z0-9]", "", username.lower())
        self.reserv = int(reservatorio) if reservatorio != None else reservatorio

        try:
            if self.reserv != None:
                self.data = c.execute(f"""
                    SELECT Q.* FROM reuse.agua_ph Q, reuse.sensores S, reuse.reservatorio R
                    WHERE Q.sensor = S.id AND
                    S.usuario = '{self.username}' AND
                    Q.reserv = {self.reserv}
                    ORDER BY Q.updated ASC, Q.sensor
                    """).fetchall()
            else:
                self.data = c.execute(f"""
                    SELECT Q.* FROM reuse.agua_ph Q, reuse.sensores S
                    WHERE Q.sensor = S.id AND
                    S.usuario = '{self.username}'
                    ORDER BY Q.updated ASC, Q.sensor
                    """).fetchall()

            if self.data == None or len(self.data) == 0:
                return {"ERROR":"Sem dados para processar"}
            else:
                self.sensores = {}
                for x in self.data:
                    self.sensores[x[1]]["id"] = x[0]
                    self.sensores[x[1]]["sensor"] = x[1]
                    self.sensores[x[1]]["reserv"] = x[2]
                    self.sensores[x[1]]["valor"] = x[3]
                    self.sensores[x[1]]["created"] = x[4]
                    self.sensores[x[1]]["updated"] = x[5]
                
                return self.sensores

        except Exception as e:
            raise  ValueError(e)
