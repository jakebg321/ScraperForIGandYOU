from flask import Flask, render_template, send_file, jsonify, request, session, redirect, url_for
import os
from functools import wraps
import secrets
import time

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Secure secret key for sessions

# Use a neutral access key
ACCESS_KEY = "VideoProcessor2024!"

# Store the real URLs securely
SECURE_URLS = {
    'github': 'https://github.com/jakebg321/CompletedScrape',
    'download': '/download'
}

def requires_access(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('has_access'):
            return jsonify({"error": "Access key required"}), 403
        return f(*args, **kwargs)
    return decorated_function

def generate_temp_token():
    return secrets.token_urlsafe(32)

@app.route('/')
def index():
    has_access = session.get('has_access', False)
    return render_template('index.html', has_access=has_access)

@app.route('/verify-access', methods=['POST'])
def verify_access():
    key = request.form.get('access_key')
    if key == ACCESS_KEY:
        session['has_access'] = True
        session['access_time'] = time.time()
        return jsonify({"success": True})
    return jsonify({"error": "Invalid access key"}), 403

@app.route('/download')
@requires_access
def download():
    try:
        executable_path = os.path.join('static', 'InstagramProcessor.exe')
        if os.path.exists(executable_path):
            return send_file(
                executable_path,
                as_attachment=True,
                download_name='InstagramProcessor.exe',
                mimetype='application/x-msdownload'
            )
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/get-url/<url_type>')
@requires_access
def get_url(url_type):
    # Generate a temporary token
    token = generate_temp_token()
    session[f'temp_token_{token}'] = {
        'url_type': url_type,
        'expires': time.time() + 300  # Token expires in 5 minutes
    }
    
    return jsonify({
        "token": token,
        "redirect_url": f'/redirect/{token}'
    })

@app.route('/redirect/<token>')
@requires_access
def handle_redirect(token):
    token_data = session.get(f'temp_token_{token}')
    
    if not token_data or time.time() > token_data['expires']:
        return jsonify({"error": "Invalid or expired token"}), 403
    
    # Get the real URL based on type
    url = SECURE_URLS.get(token_data['url_type'])
    
    # Clean up the used token
    session.pop(f'temp_token_{token}', None)
    
    if url:
        if url.startswith('/'):
            return redirect(url_for(url[1:]))  # For internal routes
        return redirect(url)  # For external URLs
    return jsonify({"error": "Invalid URL type"}), 400

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Optional: Add health check endpoint
@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200

# Optional: Add token cleanup
@app.before_request
def cleanup_old_tokens():
    current_time = time.time()
    keys_to_remove = []
    for key in session.keys():
        if key.startswith('temp_token_'):
            token_data = session[key]
            if current_time > token_data['expires']:
                keys_to_remove.append(key)
    for key in keys_to_remove:
        session.pop(key, None)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)