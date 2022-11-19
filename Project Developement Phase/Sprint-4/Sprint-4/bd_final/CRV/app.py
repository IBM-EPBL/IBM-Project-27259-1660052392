from flask import Flask, render_template, request, redirect, url_for, session, redirect, Response,flash
import requests
import ibm_db
import pandas as pd
import numpy as np
import pickle
from sklearn.preprocessing import LabelEncoder  
from flask_mail import Mail,Message
import numpy as np 
import matplotlib.pyplot as plt 

# from flask_session import Session

app=Flask(__name__)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT']=465
app.config['MAIL_USERNAME']="2k19cse075@kiot.ac.in"
app.config['MAIL_PASSWORD']="2k075cse19"
app.config['MAIL_USE_TLS']=False
app.config['MAIL_USE_SSL']=True

mail=Mail(app)

app.secret_key='r'

global email

@app.route('/')
@app.route('/entry')
def entry():
    return render_template('index.html')

##connecting database db2
conn = None

try:
    conn = ibm_db.connect("DATABASE=bludb;HOSTNAME=824dfd4d-99de-440d-9991-629c01b3832d.bs2io90l08kqb1od8lcg.databases.appdomain.cloud;PORT=30119;SECURITY=SSL;SSLServerCertificate=DigiCertGlobalRootCA.crt;UID=rpw39083;PWD=V7tkkK8SHe1YYXjy;PROTOCOL=TCPIP",'','')
    print("Successfully connected with db2")
except:
    print("Unable to connect: ", ibm_db.conn_errormsg())

##Google authentication:
# starts here    
GOOGLE_CLIENT_ID = "564634383443-f47nsem7k4kl0julaj8j1bn1fkcf3t71.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
REDIRECT_URI = '/google/auth'

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
##ends here

#sample redirects
# @app.route("/adduser",methods=["POST"])
# def adduser():
#     return render_template("main.html")

@app.route("/details",methods=["POST","GET"])
def details():
    return render_template("main.html")

## Register function
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

## Login function
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
            # name = account['NAME']
            return redirect(url_for('details'))
        else:
            if(password == account['PASSWORD']):
                # username = account['USERNAME']
                userid = account['EMAIL']
            
                # session['username'] = username
                session['userid'] = userid
                return redirect(url_for('entry'))
            else:
                return render_template('index.html', msg="Please enter the correct password")

#log out function
@app.route('/exit')
def exit():
    session.clear()
    # session.pop('name', default=None)
    session.pop('email', default=None)
    return redirect(url_for('entry'))

##prediction code
filename ='resales.sav'
model_rand=pickle.load(open(filename,'rb'))

@app.route('/result', methods = ['GET','POST'])
def result():       
    vehicleage = int(request.form['vehicle_age'])
    Km = int(request.form['Km_driven'])
    mileage1 = float(request.form['mileage'])
    engine1 = int(request.form['engine'])
    seats1 = int(request.form['seats'])
    maxpower = float(request.form['max_power'])
    ownertype = int(request.form['owner_type'])
    brand1 = request.form['slct1']
    model1 = request.form['slct2']
    fuel = request.form['fuel_type']
    transmissiontype =request.form['transmission_type']
   
    new_row = {'brand': brand1, 'model':model1,'vehicle_age':vehicleage,'km_driven':Km,'fuel_type':fuel,'transmission_type':transmissiontype,'mileage':mileage1,'engine':engine1,'max_power':maxpower,'seats':seats1,'Owner_type':ownertype}
    print(new_row)
    colunm= ['brand','model','vehicle_age','km_driven','fuel_type','transmission_type','mileage','engine','max_power','seats','Owner_type']
    new_df=pd.DataFrame(colunm) 
    print(new_df) 
    new_df = new_df.append(new_row,ignore_index=True)
    print()
    labels = ['brand','model','fuel_type','transmission_type']
    mapper={}
    for i in labels:
        mapper[i] = LabelEncoder()
        mapper[i].classes = np.load(str('classes' +i+'.npy'),allow_pickle = True)
        tr=mapper[i].fit_transform(new_df[i])
        # print(tr)
        new_df.loc[:,i + '_labels'] = pd.Series(tr,index=new_df.index)
        # print(new_df)

    new_df.dropna(subset=["brand","model"],inplace=True)
    print(new_df)
    print("*******************************************")
    labeled=new_df[['vehicle_age','km_driven','mileage','engine','max_power','seats','Owner_type']+[x+"_labels" for x in labels]]
    X= labeled.values
    print(X)
    print("------------------------------------")
    y_prediction = model_rand.predict(X)
    print(y_prediction)
    output = round(y_prediction[0],2)

    ##chart code
    if request.method=="POST":
        X = ['mileage','engine','max_power']
        user = [mileage1,engine1,maxpower]
        X_axis = np.arange(len(X))

        if(brand1=='Maruti'):
            max=[23.649,82.11,1202]
        elif(brand1=='Hyundai'):
            max=[18.77,103.36,1307]
        elif(brand1=='Ford'):
            max=[19.37,103.34,1421]
        elif(brand1=='Renault'):
            max=[18.03,81.02,1165]
        elif(brand1=='Mercedes-Benz'):
            max=[13.35,196.45,1743]
        elif(brand1=='Volkswagen'):
            max=[17.57,91.81,999]
        elif(brand1=='Honda'):
            max=[20.15,109.04,1581]
        elif(brand1=='Mahindra'):
            max=[17.39,114.32,1609]
        elif(brand1=='Datsun'):
            max=[20.76,65.83,995]
        elif(brand1=='Tata'):
            max=[21.13,112.83,1530]
        elif(brand1=='Kia'):
            max=[18,113.43,1495]
        elif(brand1=='Audi'):
            max=[16,214.52,1991]
        elif(brand1=='Skoda'):
            max=[16.60,161.37,1655]
        elif(brand1=='Bmw'):
            max=[15.66,272.67,2330]
        elif(brand1=='Toyota'):
            max=[13.34,108.05,1563]
        elif(brand1=='Nissan'):
            max=[14.33,123.28,1746]
        elif(brand1=='Jeep'):
            max=[14.9,167.67,1956]
        elif(brand1=='Volvo'):
            max=[11.2,246.74,1998]
        elif(brand1=='Volvo'):
            max=[15.6,120.76,1598]
        else:
            max=[0,0,0,]
        plt.bar(X_axis - 0.2, max, 0.4, label = 'max_value')
        plt.bar(X_axis + 0.2, user, 0.4, label = 'user')

        plt.savefig('png.png')
  
        plt.xticks(X_axis, X)
        plt.xlabel("user")
        plt.ylabel("values")
        plt.legend()
        print("saved successfully")
        message=Message('Chart',sender="2k19cse075@kiot.ac.in",recipients=["2k19cse075@kiot.ac.in"])
        with app.open_resource("png.png") as fp:
            message.attach("png.png", "png/png", fp.read())
        mail.send(message)

    return render_template('main.html',prediction="{} Rupees".format(output))

if __name__ =='__main__':
    app.run()