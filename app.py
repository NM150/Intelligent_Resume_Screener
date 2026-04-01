"""
Complete Flask Application with BERT Resume Screener
This replaces your entire backend with BERT-powered matching
"""
from flask import Flask, request, render_template, jsonify
from werkzeug.utils import secure_filename
import os
import PyPDF2
import docx
from bert_screener import BERTResumeScreener

app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

# Initialize BERT screener (happens once when server starts)
print("Initializing BERT Resume Screener...")
screener = BERTResumeScreener()
print("✓ Ready to screen resumes!")

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file."""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
    return text

def extract_text_from_docx(docx_path):
    """Extract text from DOCX file."""
    text = ""
    try:
        doc = docx.Document(docx_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    except Exception as e:
        print(f"Error reading DOCX {docx_path}: {e}")
    return text

def extract_text_from_txt(txt_path):
    """Extract text from TXT file."""
    try:
        with open(txt_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        print(f"Error reading TXT {txt_path}: {e}")
        return ""

def process_resume_file(file_path, filename):
    """Extract text from resume based on file type."""
    extension = filename.rsplit('.', 1)[1].lower()
    
    if extension == 'pdf':
        return extract_text_from_pdf(file_path)
    elif extension == 'docx':
        return extract_text_from_docx(file_path)
    elif extension == 'txt':
        return extract_text_from_txt(file_path)
    else:
        return ""

@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@app.route('/matcher', methods=['POST'])
def matcher():
    """
    Main endpoint for BERT-based resume matching.
    This is what gets called when the form is submitted.
    """
    try:
        # Get job description from form
        job_description = request.form.get('job_description', '').strip()
        
        if not job_description:
            return render_template('index.html', 
                                 message="⚠️ Please provide a job description.")
        
        # Get uploaded resume files
        files = request.files.getlist('resumes')
        
        if not files or len(files) < 5:
            return render_template('index.html', 
                                 message="⚠️ Please upload at least 5 resumes.")
        
        # Create upload directory if needed
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # Process all uploaded resumes
        resumes = {}
        failed_files = []
        
        for file in files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # Save file temporarily
                file.save(file_path)
                
                # Extract text from resume
                resume_text = process_resume_file(file_path, filename)
                
                if resume_text and len(resume_text.strip()) > 50:
                    resumes[filename] = resume_text
                else:
                    failed_files.append(filename)
                
                # Delete temporary file
                try:
                    os.remove(file_path)
                except:
                    pass
        
        # Check if we have enough valid resumes
        if len(resumes) < 5:
            message = f"⚠️ Only {len(resumes)} valid resumes processed. "
            message += f"Please upload at least 5 resumes with readable text."
            if failed_files:
                message += f" Failed to process: {', '.join(failed_files[:3])}"
            return render_template('index.html', message=message)
        
        # ============================================================
        # BERT MAGIC HAPPENS HERE! 🚀
        # ============================================================
        
        # Rank resumes using BERT
        results = screener.rank_resumes(job_description, resumes, top_k=3)
        
        # Prepare data for display
        top_resumes = []
        similarity_scores = []
        
        for resume_name, score in results:
            top_resumes.append(resume_name)
            # Convert to percentage for display
            similarity_scores.append(f"{score * 100:.2f}")
        
        # Return results to frontend
        return render_template('index.html',
                             message="🎉 Top 3 Best Matching Candidates",
                             top_resumes=top_resumes,
                             similarity_scores=similarity_scores)
    
    except Exception as e:
        print(f"Error in matcher: {str(e)}")
        import traceback
        traceback.print_exc()
        return render_template('index.html', 
                             message=f"❌ Error: {str(e)}")


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'model': 'BERT (Sentence-BERT)',
        'version': '1.0'
    })

if __name__ == '__main__':
    # Run the Flask app
    print("\n" + "="*60)
    print("🚀 BERT Resume Screener Server Starting...")
    print("="*60)
    print("\nServer will be available at: http://localhost:5000")
    #print("Press Ctrl+C to stop the server\n")
    
    # Development mode
    app.run(debug=True, host='0.0.0.0', port=5000)