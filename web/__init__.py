from flask import Flask
import json
import os
#import web.mail

app = Flask(__name__, 
        static_url_path="", 
        static_folder="templates/static",
        )

import web.views



BASE_DIR=os.path.dirname(os.path.dirname(__file__))

with open(os.path.dirname(os.path.dirname(__file__)) + "/.env.json") as db:
        js = json.load(db)
        app.config["SECRET_KEY"]= js['CONFIG']['SECRET_KEY']
        
        app.config['MAIL_SERVER']= js['MAIL']["MAIL_SERVER"]
        app.config['MAIL_PORT'] = js['MAIL']['MAIL_PORT']
        app.config['MAIL_USERNAME'] = js['MAIL']['MAIL_USERNAME']
        app.config['MAIL_PASSWORD'] = js['MAIL']["MAIL_PASSWORD"] #os.environ.get('MAIL_PASSWORD')
        app.config['MAIL_USE_TLS'] =  js['MAIL']["MAIL_USE_TLS"]
        app.config['MAIL_USE_SSL'] =   js['MAIL']["MAIL_USE_SSL"]
        app.config['MAIL_DEFAULT_SENDER'] =  js['MAIL']["MAIL_USERNAME"]
