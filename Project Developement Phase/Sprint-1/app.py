from flask import Flask, render_template, request, redirect, url_for, session, redirect, request
import requests
import ibm_db
app=Flask(__name__)

GOOGLE_CLIENT_ID = "564634383443-f47nsem7k4kl0julaj8j1bn1fkcf3t71.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
REDIRECT_URI = '/google/auth'

conn = None

##connecting database db2
try:
    conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=824dfd4d-99de-440d-9991-629c01b3832d.bs2io90l08kqb1od8lcg.databases.appdomain.cloud;PORT=30119;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=rpw39083;PWD=V7tkkK8SHe1YYXjy;PROTOCOL=TCPIP",'','')
    print("Successfully connected with db2")
except:
    print("Unable to connect: ", ibm_db.conn_errormsg())


@app.route('/')
@app.route('/entry')
def entry():
    return render_template('index.html')

##Google authentication:    
@app.route("/google")
def google():
    return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?scope=https://www.googleapis.com/auth/userinfo.profile&access_type=offline&include_granted_scopes=true&response_type=code&redirect_uri=http://127.0.0.1:5000/google/auth&client_id={GOOGLE_CLIENT_ID}")

@app.route("/google/auth")
def google_auth():
    r = requests.post("https://oauth2.googleapis.com/token", 
    data={
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": request.args.get("code"),
        "grant_type": "authorization_code",
        "redirect_uri": "http://127.0.0.1:5000/google/auth"
    })
    r = requests.get(f'https://www.googleapis.com/oauth2/v2/userinfo?access_token={r.json()["access_token"]}').json()

    print(r)
    return redirect("/details")   


@app.route("/adduser", methods=["POST"])
def adduser():
    name = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    mobilenumber= request.form.get("mobilenumber")
    
    sql = "SELECT * FROM register WHERE email = ?" 
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt, 1, email)
    ibm_db.execute(stmt)
    account = ibm_db.fetch_assoc(stmt)

    if account:
        return render_template('index.html', msg="You are already a member, please login using your details")
    else:
        insert_sql = "INSERT INTO register VALUES (?,?,?,?)"
        prep_stmt = ibm_db.prepare(conn, insert_sql)
        ibm_db.bind_param(prep_stmt, 1, email)
        ibm_db.bind_param(prep_stmt, 2, name)
        ibm_db.bind_param(prep_stmt, 3, password)
        ibm_db.bind_param(prep_stmt, 4, mobilenumber)
        ibm_db.execute(prep_stmt)
        return render_template('index.html', msg="You are Successfully Registered with IMS, please login using your details")


@app.route("/login", methods=["POST"])
def login():
    email = request.form.get("email")
    password = request.form.get("password")
    sql = "SELECT * FROM register WHERE email = ?" 
    stmt = ibm_db.prepare(conn, sql)
    ibm_db.bind_param(stmt, 1, email)
    ibm_db.execute(stmt)
    account = ibm_db.fetch_assoc(stmt)
    if not account:
        return render_template('index.html', msg="You are not yet registered, please sign up using your details")
    else:
        if(password == account['PASSWORD']):
            email = account['EMAIL']
            name = account['NAME']
            return redirect(url_for('details'))
        else:
            return render_template('index.html', msg="Please enter the correct password")

@app.route("/details")
def details():
    return render_template('main.html') 

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

