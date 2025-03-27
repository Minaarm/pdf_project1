from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
import PyPDF2

app = Flask(__name__)

# Configure Database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pdf_data.db'
app.config['UPLOAD_FOLDER'] = './uploads'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database model
class PDFData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(100), nullable=False)
    text_content = db.Column(db.Text, nullable=True)
    upload_date = db.Column(db.DateTime, default=db.func.current_timestamp())

# Endpoint to upload PDFs
@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    if file:
        # Save PDF
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # Extract text from PDF
        text_content = extract_text(file_path)

        # Save to database
        pdf_data = PDFData(file_name=file.filename, text_content=text_content)
        db.session.add(pdf_data)
        db.session.commit()

        return jsonify({'message': 'File uploaded and processed successfully'}), 200

# Function to extract text using PyPDF2
def extract_text(file_path):
    with open(file_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    return text

# Endpoint to search PDFs
@app.route('/search', methods=['GET'])
def search_pdfs():
    query = request.args.get('query', '')
    if not query:
        return jsonify({'message': 'Please provide a search query'}), 400

    results = PDFData.query.filter(PDFData.text_content.ilike(f'%{query}%')).all()

    result_list = [{'file_name': pdf.file_name, 'upload_date': pdf.upload_date} for pdf in results]

    return jsonify({'results': result_list}), 200

if __name__ == '__main__':
    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Create database tables
    with app.app_context():
        db.create_all()
    
    app.run(debug=True)
