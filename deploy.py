from pyinfra.operations import apt, server, files, git, pip, systemd, postgres, postgresql
from pyinfra import host
from pyinfra.facts.postgres import PostgresDatabases
from pyinfra.facts.files import Directory, FindDirectories
from pyinfra import logger
from pyinfra.operations import python

ERVINIZMUS_HTML_DEST = "/var/www/ervinizmus"

POSTGRES_DB_NAME = "ervinizmus"
POSTGRES_NAME = "danidb"
POSTGRES_PASSWORD = "EzEgyAdatbazis11"

def log(string=None):
    logger.error(string)

# Define some state - this operation will do nothing on subsequent runs
apt.packages(
    name="APT csomagok telepítése.",
    packages=["vim", "mc", "net-tools", "apache2", "python3", "python3-pip",
              "net-tools", "git", "certbot", "python3-virtualenv", "libapache2-mod-wsgi-py3", "postgresql"],
    update=True,
)

files.file(
    name="Create pyinfra log file",
    path="/home/pyinfra.log",
    user="dani",
    group="dani",
    mode="644",
    _sudo=True,
)




git.repo(
    name="Ervinizmus letöltése",
    src="https://github.com/d-b-v-project/weboldal.git",
    dest="/var/www/ervinizmus"
)


files.template(
    name="Ervinizmus_template betöltés",
    src="templates/ervinizmus_apache2.conf.j2",
    dest="/etc/apache2/sites-available/ervinizmus.conf",
    ERVINIZMUS_HTML_DEST=ERVINIZMUS_HTML_DEST
)

files.template(
    name="wsgihandler template betöltés",
    src="templates/wsgihandler.py.j2",
    dest=f"{ERVINIZMUS_HTML_DEST}/wsgihandler.py",
    ERVINIZMUS_HTML_DEST=ERVINIZMUS_HTML_DEST
)

files.template(
    name="key.py template betöltés",
    src="templates/key.py.j2",
    dest=f"{ERVINIZMUS_HTML_DEST}/key.py",
)




files.template(
    name="cert.pem betöltése",
    src="templates/cert.pem.j2",
    dest="/etc/letsencrypt/live/ervinizmus.eu/cert.pem"
)

files.template(
    name="chain.pem betöltése",
    src="templates/chain.pem.j2",
    dest="/etc/letsencrypt/live/ervinizmus.eu/chain.pem"
)
files.template(
    name="fullchain.pem betöltése",
    src="templates/fullchain.pem.j2",
    dest="/etc/letsencrypt/live/ervinizmus.eu/fullchain.pem"
)
files.template(
    name="privkey.pem betöltése",
    src="templates/privkey.pem.j2",
    dest="/etc/letsencrypt/live/ervinizmus.eu/privkey.pem"
)



files.directory(
    name="Ervinizmus.eu létrehozása",
    path="/var/log/apache2/ervinizmus.eu/"
)

server.shell(
    name="Engedélyezni az apache2 configot",
    commands=["a2ensite ervinizmus"]
)

server.shell(
    name="Engedélyezni az apache2 modult",
    commands=["a2enmod rewrite ssl wsgi"]
)



files.directory(
    name="Apache2 log létrehozás",
    path="/var/log/ervinizmus.eu"
)

pip.packages(
    name="Python függőségek telepítése.",
    packages=["blinker==1.9.0"
              ,"certifi==2025.1.31", "chardet==5.2.0", "charset-normalizer==3.4.1"
              ,"click==8.1.8"
              ,"Flask==3.1.0"
              ,"Flask-Mail==0.10.0"
              ,"idna==3.10"
              ,"itsdangerous==2.2.0"
              ,"Jinja2==3.1.6"
              ,"MarkupSafe==3.0.2"
              ,"numpy==2.2.3"
              ,"pillow==11.1.0"
              ,"psycopg2-binary==2.9.10"
              ,"pydub==0.25.1"
              ,"PyPDF2==3.0.1"
              ,"python-core==0.0.1"
              ,"reportlab==4.3.1"
              ,"requests==2.32.3"
              ,"SpeechRecognition==3.14.1"
              ,"typing_extensions==4.12.2"
              ,"urllib3==2.3.0"
              ,"Werkzeug==3.1.3"],
    virtualenv=f"{ERVINIZMUS_HTML_DEST}/venv"
)


print(host.get_fact(FindDirectories, path="/etc/leletsencrypt"))

"""files.directory(
    name="live mappa létrehozása."
)"""


server.shell(
    name="Apache2 konfiguráció ellenőrzése.",
    commands=["apache2ctl configtest"]
)

systemd.service(
    service="apache2",
    enabled=True,
    restarted=True
)

postgresql.role(
    name="PostgreSQL fiók létrehozása",
    role=POSTGRES_NAME,
    password=POSTGRES_PASSWORD,
    superuser=True,
    login=True,
    _sudo_user="postgres",
    
)

is_db_exist = postgres.sql(
    name="Ervinizmus db létezik?",
    sql="SELECT * FROM hivok",
    psql_database=POSTGRES_DB_NAME,
    psql_host="localhost",
    psql_user=POSTGRES_NAME,
    psql_password=POSTGRES_PASSWORD,
    _ignore_errors=True
)

python.call(
    name="Result...",
    function=log,
    string=str(is_db_exist)
)


postgres.database(
    name="Ervinizmus adatbázis létrehozása.",
    database=POSTGRES_DB_NAME,
    owner=POSTGRES_NAME,
    encoding="UTF8",
    _sudo_user="postgres",
    _if=is_db_exist.did_error
)

files.put(
    name="Ervinizmus dump másolása a távoli gépre.",
    src="files/ervinizmus_db.dump",
    dest="/tmp",
    _if=is_db_exist.did_error
)

postgres.load(
    name="Postgresql dump betöltése",
    src="/tmp/ervinizmus_db.dump",
    psql_database=POSTGRES_DB_NAME,
    _sudo_user="postgres",
    #psql_user = POSTGRES_NAME,
    #psql_password = POSTGRES_PASSWORD,
    #psql_host = "localhost"
    _if=is_db_exist.did_error
)



