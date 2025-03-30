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
    
    # Save the uploaded file
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    
    # Extract text from the uploaded PDF
    text_content = extract_text(file_path)  # Call the function to extract text

    # Save to the database
    pdf_data = PDFData(file_name=file.filename, text_content=text_content)
    db.session.add(pdf_data)
    db.session.commit()

    return jsonify({
        'message': 'File uploaded and processed successfully',
        'extracted_text': text_content  # Include the extracted text in the response
    }), 200

# Function to extract text using PyPDF2
def extract_text(file_path):
    with open(file_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
    
    # Add a fallback message if no text is extracted
    if not text.strip():
        text = "No text content could be extracted from this PDF."
    
    return text

# Endpoint to search PDFs
@app.route('/search', methods=['GET'])
def search_pdfs():
    query = request.args.get('query', '')
    limit = int(request.args.get('limit', 10))  # Default limit is 10
    offset = int(request.args.get('offset', 0))  # Default offset is 0
    
    if not query:
        return jsonify({'message': 'Please provide a search query'}), 400

    results = PDFData.query.filter(PDFData.text_content.ilike(f'%{query}%')).limit(limit).offset(offset).all()

    # Add a snippet of matching text to each result
    result_list = [{
        'file_name': pdf.file_name,
        'upload_date': pdf.upload_date,
        'snippet': pdf.text_content[:100]  # First 100 characters as a preview
    } for pdf in results]

    return jsonify({'results': result_list}), 200

if __name__ == '__main__':
    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Create database tables
    with app.app_context():
        db.create_all()
    
    app.run(debug=True)
