CREATE SCHEMA IF NOT EXISTS reuse;
SET TIMEZONE TO 'America/Sao_Paulo';

 CREATE TABLE IF NOT EXISTS reuse.sensores(
     id         		SERIAL  PRIMARY KEY,
     nome       		VARCHAR(50) NOT NULL,
     tipo       		VARCHAR(50),
     pino       		INTEGER NOT NULL CHECK(pino > 0 AND pino < 100),
     usuario 		    VARCHAR(20) NOT NULL,
     created    	    TIMESTAMPTZ DEFAULT now(),
     updated    	    TIMESTAMPTZ DEFAULT now(),
     deleted		    BOOLEAN DEFAULT FALSE,
     FOREIGN KEY (usuario) REFERENCES  reuse.usuarios(username)
     );

 CREATE TABLE IF NOT EXISTS reuse.active_sensor(
     id         		SERIAL  PRIMARY KEY,
     sensor     		INTEGER NOT NULL,
     status     		CHAR(1) CHECK(status = 'A' OR status = 'F' OR status='I'), -- A=Aberto, F=Fechado, I=Inativo,
     created  		    TIMESTAMPTZ DEFAULT now(),
     updated    	    TIMESTAMPTZ DEFAULT now(),
     FOREIGN KEY (sensor) REFERENCES  reuse.sensores(id)
     );


 CREATE TABLE IF NOT EXISTS reuse.reservatorio(
     id         		SERIAL  PRIMARY KEY,
     nome       		VARCHAR(50) NOT NULL,
     tipo       		CHAR(1) CHECK(tipo='C' OR tipo='T'),
     capacidade 	    NUMERIC(6,0) NOT NULL CHECK(capacidade>0),
     usuario            VARCHAR(20) NOT NULL,
     created    	    TIMESTAMPTZ DEFAULT now(),
     updated    	    TIMESTAMPTZ DEFAULT now(),
     deleted		    BOOLEAN DEFAULT FALSE,
     FOREIGN KEY (usuario) REFERENCES  reuse.usuarios(username)
     );


 CREATE TABLE IF NOT EXISTS reuse.agua_quantity(
     id         		SERIAL  PRIMARY KEY,
     sensor     		INTEGER NOT NULL,
     reserv     		INTEGER NOT NULL,
     valor      		NUMERIC(4,2) NOT NULL,
     created    	    TIMESTAMPTZ DEFAULT now(),
     updated    	    TIMESTAMPTZ DEFAULT now(),
     FOREIGN KEY (sensor) REFERENCES  reuse.sensores(id),
     FOREIGN KEY (reserv) REFERENCES  reuse.reservatorio(id)
     );

 CREATE TABLE IF NOT EXISTS reuse.agua_ph(
     id         		SERIAL  PRIMARY KEY,
     sensor     		INTEGER NOT NULL,
     reserv     		INTEGER NOT NULL,
     valor      		NUMERIC(4,2) NOT NULL,
     created    	    TIMESTAMPTZ DEFAULT now(),
     updated    	    TIMESTAMPTZ DEFAULT now(),
     FOREIGN KEY (sensor) REFERENCES  reuse.sensores(id),
     FOREIGN KEY (reserv) REFERENCES  reuse.reservatorio(id)
     );

 CREATE TABLE IF NOT EXISTS reuse.fluxo_agua(
     id         		SERIAL  PRIMARY KEY,
     sensor     		INTEGER NOT NULL,
     litros     		NUMERIC(4,2) NOT NULL,
     created    	    TIMESTAMPTZ DEFAULT now(),
     updated    	    TIMESTAMPTZ DEFAULT now(),
     FOREIGN KEY (sensor) REFERENCES  reuse.sensores(id)
    );

 CREATE TABLE IF NOT EXISTS reuse.usuarios(
 	id         		SERIAL  PRIMARY KEY,
 	nome 		    VARCHAR(50) NOT NULL,
 	username 	    VARCHAR(20) UNIQUE NOT NULL,
 	senha 		    VARCHAR(200) NOT NULL,
 	senha_old 	    VARCHAR(200),
 	email 		    VARCHAR(100) UNIQUE NOT NULL,
 	deleted		    BOOLEAN DEFAULT FALSE,
 	created 	    TIMESTAMPTZ DEFAULT now(),
 	updated 	    TIMESTAMPTZ DEFAULT now()
 );

 CREATE TABLE IF NOT EXISTS reuse.logs_sensores(
 	id 			    SERIAL  PRIMARY KEY,
 	usuario 		VARCHAR(20) NOT NULL,
 	ip 			    VARCHAR(30),
 	sensor 		    INTEGER NOT NULL,
 	datahora 	    TIMESTAMPTZ DEFAULT now() NOT NULL,
 	FOREIGN KEY (sensor) 	REFERENCES  reuse.sensores(id),
 	FOREIGN KEY (usuario) 	REFERENCES  reuse.usuarios(username)
 );

  CREATE TABLE IF NOT EXISTS reuse.logs_reservatorio(
 	id 				SERIAL  PRIMARY KEY,
 	usuario 		VARCHAR(20) NOT NULL,
 	ip 				VARCHAR(30),
 	reserv 			INTEGER NOT NULL,
 	datahora 		TIMESTAMPTZ DEFAULT now() NOT NULL,
 	FOREIGN KEY (reserv) 	REFERENCES  reuse.reservatorio(id),
 	FOREIGN KEY (usuario) 	REFERENCES  reuse.usuarios(username)
 );

 CREATE TABLE IF NOT EXISTS reuse.logs_acessos(
 	id         		SERIAL  PRIMARY KEY,
 	usuario	 	    VARCHAR(20) NOT NULL,
 	ip 			    VARCHAR(30),
    logs            VARCHAR(200),
 	datahora 	    TIMESTAMPTZ DEFAULT now() NOT NULL,
 	FOREIGN KEY (usuario) REFERENCES  reuse.usuarios(username)
 );

 CREATE TABLE IF NOT EXISTS reuse.access_token(
 	id 			        SERIAL  PRIMARY KEY,
 	token 		        VARCHAR(50) 	NOT NULL UNIQUE,
 	expira 		        DATE 		NOT NULL DEFAULT (NOW() + INTERVAL '30 DAYS'),
 	usuario 		    VARCHAR(20) NOT NULL UNIQUE,
    created    	    TIMESTAMPTZ DEFAULT now(),
    updated    	    TIMESTAMPTZ DEFAULT now(),
 	FOREIGN KEY (usuario) REFERENCES  reuse.usuarios(username)
 );

 CREATE TABLE IF NOT EXISTS reuse.reset_senha(
 	usuario 		VARCHAR(20) NOT NULL,
 	token 		    CHAR(6) NOT NULL,
 	expira 		    TIMESTAMPTZ DEFAULT (now() + interval '15 MINUTE'),
 	created 	    TIMESTAMPTZ DEFAULT now(),
 	used		    BOOLEAN DEFAULT 'FALSE',
 	FOREIGN KEY (usuario) REFERENCES  reuse.usuarios(username)
 );
