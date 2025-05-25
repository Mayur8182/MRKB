from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Test Server Running on Port 5003"

@app.route('/test')
def test():
    return "Test Route Working"

if __name__ == '__main__':
    print("Starting test server...")
    app.run(debug=True, port=5003, host='127.0.0.1')
