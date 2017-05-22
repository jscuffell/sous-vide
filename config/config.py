from flask import Flask
from flask import render_template
app = Flask(__name__)

@app.route('/')
def hello_world():
    ssids_input = ['hello', 'hello2', 'hello3']
    return render_template('index.html', ssids=ssids_input)

if __name__ == '__main__':
    app.run(host='0.0.0.0')
