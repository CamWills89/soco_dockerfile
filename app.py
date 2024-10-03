from flask import Flask,jsonify,request

from agent import main

app = Flask(__name__)

@app.route('/')
def test():
    print("test")

@app.route('/generate', methods=['POST'])
def generate():
    params = request.json
    response=main(params['input'])
    return jsonify({
    "headers": {
        "Content-Type": "application/json",
    },
    "statusCode": 200,
    "body": response
    })
###{"input":"On September 26, 2024, at 1:00 PM, elevated user secure_user attempted to log into secure_access_db but failed both password entry and two-factor authentication, resulting in 10 consecutive failed attempts within 10 minutes."}
if __name__ == "__main__":
    app.run(port=8080,debug=True)