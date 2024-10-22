from flask import Flask, render_template, send_from_directory, send_file, jsonify
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download')
def download():
    try:
        # Define the path to your executable
        executable_path = os.path.join('static', 'InstagramProcessor.exe')
        
        # Check if the file exists
        if os.path.exists(executable_path):
            return send_file(
                executable_path,
                as_attachment=True,
                download_name='InstagramProcessor.exe',
                mimetype='application/x-msdownload'
            )
        else:
            return jsonify({
                "error": "Download file not found. Please try again later or download from GitHub."
            }), 404
    except Exception as e:
        return jsonify({
            "error": f"Download failed. Please try downloading from GitHub: {str(e)}"
        }), 500

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)