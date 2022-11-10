from flask import Flask, render_template, request, redirect, url_for, session, redirect
import requests

GOOGLE_CLIENT_ID = "564634383443-f47nsem7k4kl0julaj8j1bn1fkcf3t71.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
REDIRECT_URI = '/google/auth'

app=Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route("/main")
def main():
    return render_template("main.html")

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
    return redirect("/main")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)