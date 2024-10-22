from flask import Flask, render_template, send_from_directory, jsonify
import os
import platform

app = Flask(__name__)
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download')
def download():
    # Check if we're running on Windows
    if platform.system() == 'Windows':
        return send_from_directory('static', 'InstagramVideoProcessor.exe', as_attachment=True)
    else:
        return jsonify({
            "error": "Direct downloads are only available for Windows. Please visit the GitHub repository for other platforms."
        }), 400

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)