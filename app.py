from flask import Flask, render_template, send_from_directory, send_file
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download/windows')
def download_windows():
    return send_file(
        'static/InstagramProcessor.exe',
        as_attachment=True,
        download_name='InstagramProcessor.exe'
    )

@app.route('/download/mac')
def download_mac():
    return send_file(
        'static/InstagramProcessor.dmg',
        as_attachment=True,
        download_name='InstagramProcessor.dmg'
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)