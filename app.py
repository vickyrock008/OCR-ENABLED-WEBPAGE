from flask import Flask, request, send_file, render_template, redirect, url_for, session, jsonify
import pytesseract as pyt
import cv2
import gtts as gt
import os
import time
from langdetect import detect
from fpdf import FPDF
from docx import Document
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configure app using environment variables
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///users.db')  # Default to SQLite if not set
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS', False)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret_key')

# Initialize database
db = SQLAlchemy(app)

# Create User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password = db.Column(db.String(150), nullable=False)

# Create ExtractedText model
class ExtractedText(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())

# Home Page Route
@app.route('/')
def index():
    return render_template('index.html')  # Return the homepage template

# Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')  # Secure password hashing
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))  # Redirect to login after successful registration
    return render_template('register.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):  # Check if user exists and passwords match
            session['user_id'] = user.id  # Save user session
            return redirect(url_for('index'))  # Redirect to homepage after successful login
        return 'Invalid username or password'  # Handle failed login
    return render_template('login.html')

# Logout Route
@app.route('/logout')
def logout():
    session.pop('user_id', None)  # Remove user session
    return redirect(url_for('index'))  # Redirect to home page after logout

# Set up Tesseract command path
pyt.pytesseract.tesseract_cmd = os.getenv('TESSERACT_CMD', 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe')

# Custom Tesseract config
custom_config = f"--oem 1 --psm 6 --tessdata-dir '{os.getenv('TESSDATA_DIR', 'C:\\Program Files\\Tesseract-OCR\\tessdata')}' --dpi 300"

# Directory to save temporary files
TEMP_DIR = os.getenv('TEMP_DIR', 'temp_files')
if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

# Extract Text and Generate Audio
def extract_text_and_audio(image_path, selected_language):
    image = cv2.imread(image_path)
    if image is None:
        return "Image loading failed", None

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 41, 5
    )

    # OCR
    text = pyt.image_to_string(thresh, lang=selected_language, config=custom_config).strip()
    if not text:
        return "No text detected", None

    # Language Mapping for TTS
    language_mapping = {
        'eng': 'en', 'de': 'de', 'fr': 'fr', 'hi': 'hi',
        'ru': 'ru', 'es': 'es', 'ta': 'ta',
    }
    tts_language = language_mapping.get(selected_language, 'en')

    # TTS Audio Generation
    audio_filename = f"extracted_text_audio_{int(time.time())}.mp3"
    audio_path = os.path.join(TEMP_DIR, audio_filename)

    tts = gt.gTTS(text=text, lang=tts_language, slow=False)
    tts.save(audio_path)

    return text, audio_path

# Extract Text Route
@app.route('/image_text_to_audio', methods=['POST'])
def image_text_to_audio_route():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if user is not authenticated

    user_id = session['user_id']
    image_file = request.files['image']
    selected_language = request.form.get('language', 'eng')
    image_path = os.path.join(TEMP_DIR, "temp_image.png")
    image_file.save(image_path)

    text, audio_path = extract_text_and_audio(image_path, selected_language)
    if text in ["Image loading failed", "No text detected"]:
        return jsonify({"text": text, "audio_url": ""})

    # Save the extracted text to the database
    extracted_text = ExtractedText(user_id=user_id, text=text)
    db.session.add(extracted_text)
    db.session.commit()

    return jsonify({"text": text, "audio_url": f"/download_audio/{os.path.basename(audio_path)}"})

@app.route('/image_text_to_word', methods=['POST'])
def image_text_to_word():
    text = request.form['text']
    doc = Document()
    doc.add_paragraph(text)
    word_filename = f"extracted_text_{int(time.time())}.docx"
    word_path = os.path.join(TEMP_DIR, word_filename)
    doc.save(word_path)
    return send_file(word_path, as_attachment=True)

# User History Route
@app.route('/history')
def user_history():
    if 'user_id' not in session:
        return redirect(url_for('login'))  # Redirect to login if user is not authenticated

    user_id = session['user_id']
    history = ExtractedText.query.filter_by(user_id=user_id).order_by(ExtractedText.created_at.desc()).all()
    return render_template('history.html', history=history)

@app.route('/download_audio/<filename>')
def download_audio(filename):
    return send_file(os.path.join(TEMP_DIR, filename), as_attachment=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensure tables are created
    app.run(debug=True, port=5500)
