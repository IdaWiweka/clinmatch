from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from sqlalchemy.orm import joinedload
from flask_sqlalchemy import SQLAlchemy
from markupsafe import Markup
from werkzeug.security import generate_password_hash, check_password_hash
import re
import json
import os
from dotenv import load_dotenv 
from sentence_transformers import SentenceTransformer, util 
import numpy as np

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', '123456')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///entities.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Global configuration parameters
SEMANTIC_MATCH_THRESHOLD = 0.8  # Threshold for semantic matching (0-1)
FUZZY_MATCH_THRESHOLD = 80     # Threshold for fuzzy matching (0-100)

db = SQLAlchemy(app)

# Initialize the sentence transformer model with S-PubMedBert-MS-MARCO
model = SentenceTransformer('pritamdeka/S-PubMedBert-MS-MARCO')

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class MatchResult(db.Model):
    __tablename__ = 'match_result'
    id = db.Column(db.Integer, primary_key=True)
    text_id = db.Column(db.String(50), db.ForeignKey('text_index.text_id'), nullable=False)
    category = db.Column(db.String(80), nullable=False)
    entities = db.Column(db.Text, nullable=False)
    matched = db.Column(db.Text, nullable=True)
    unmatched = db.Column(db.Text, nullable=True)
    undetected_entity = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    text = db.relationship('TextIndex', backref='match_results')

    __table_args__ = (
        db.UniqueConstraint('user_id', 'text_id', 'category', name='unique_annotation'),
    )

class TextIndex(db.Model):
    __tablename__ = 'text_index'
    id = db.Column(db.Integer, primary_key=True)
    text_id = db.Column(db.String(50), unique=True, nullable=False)
    text = db.Column(db.Text, nullable=False)

def safe_read_jsonl(file_path):
    """Safely read and parse JSONL file with error handling."""
    try:
        with open(file_path, 'r') as f:
            return [json.loads(line) for line in f]
    except FileNotFoundError:
        app.logger.error(f"File not found: {file_path}")
        return []
    except json.JSONDecodeError as e:
        app.logger.error(f"JSON decode error in {file_path}: {str(e)}")
        return []
    except Exception as e:
        app.logger.error(f"Error reading {file_path}: {str(e)}")
        return []

def load_all_records_from_jsonl(file_path='database.jsonl'):
    records = []
    data = safe_read_jsonl(file_path)
    
    for record in data:
        text = record.get("text", "")
        text_id = record.get("text_id", "")
        for key, value in record.items():
            if key not in ["text", "text_id"]:
                records.append({
                    "text": text,
                    "text_id": text_id,
                    "category": key,
                    "entities": value
                })
    return records

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

def format_text_for_display(text):
    """
    Format text for better readability by:
    1. Preserving the original text format
    2. Ensuring proper spacing
    """
    try:
        # Clean up any multiple spaces
        formatted_text = re.sub(r' +', ' ', text)
        
        # Ensure proper newline handling
        formatted_text = formatted_text.replace('\n', '\r\n')
        
        print("Original text:", text)
        print("Formatted text:", formatted_text)
        
        return formatted_text
    except Exception as e:
        print(f"Error in format_text_for_display: {str(e)}")
        import traceback
        traceback.print_exc()
        return text

@app.route('/annotate/<int:text_id>')
def annotate(text_id):
    record = TextIndex.query.get(text_id)
    if not record:
        return "Text not found.", 404
    formatted_text = format_text_for_display(record.text)
    return render_template("index.html", text=formatted_text)

def get_semantic_matches(text, entities, method='sentence'):
    """
    Find matches between text and entities using either sentence transformer or fuzzy matching.
    Args:
        text: The text to search in
        entities: List of entities to find
        method: 'sentence' for sentence transformer or 'fuzzy' for fuzzy matching
    """
    try:
        print(f"\nProcessing text: {text}")
        print(f"Looking for entities: {entities}")
        print(f"Using method: {method}")
        
        # Use the global threshold based on method
        threshold = SEMANTIC_MATCH_THRESHOLD if method == 'sentence' else FUZZY_MATCH_THRESHOLD
        print(f"Using threshold: {threshold}")
        
        matches = []
        
        if method == 'sentence':
            # Get embeddings for text and entities
            text_embedding = model.encode(text, convert_to_tensor=True)
            entity_embeddings = model.encode(entities, convert_to_tensor=True)
            
            # Calculate cosine similarity
            similarities = util.pytorch_cos_sim(text_embedding, entity_embeddings)[0]
            
            print("\nDetailed similarity scores:")
            for i, entity in enumerate(entities):
                similarity = similarities[i].item()
                print(f"Entity: {entity}, Similarity: {similarity:.4f}")
                
                if similarity >= threshold:
                    # Find the position in text where this entity appears
                    # Use word boundary and case-insensitive search
                    pattern = re.compile(r'\b' + re.escape(entity) + r'\b', re.IGNORECASE)
                    match = pattern.search(text)
                    
                    match_data = {
                        'entity': entity,
                        'similarity': similarity
                    }
                    
                    if match:
                        start = match.start()
                        end = match.end()
                        matched_text = text[start:end]
                        print(f"Found exact match for '{entity}' at position {start} with similarity {similarity:.4f}")
                        print(f"Matched text: '{matched_text}'")
                        match_data.update({
                            'start': start,
                            'end': end,
                            'matched_text': matched_text
                        })
                    else:
                        print(f"No exact match found in text for '{entity}' but has high similarity {similarity:.4f}")
                    
                    matches.append(match_data)
                else:
                    print(f"Similarity {similarity:.4f} below threshold {threshold} for '{entity}'")
        
        else:  # fuzzy matching
            from fuzzywuzzy import fuzz
            
            for entity in entities:
                # Try exact match first with word boundaries
                pattern = re.compile(r'\b' + re.escape(entity) + r'\b', re.IGNORECASE)
                match = pattern.search(text)
                if match:
                    start = match.start()
                    end = match.end()
                    matched_text = text[start:end]
                    print(f"Found exact match for '{entity}'")
                    print(f"Matched text: '{matched_text}'")
                    matches.append({
                        'entity': entity,
                        'start': start,
                        'end': end,
                        'matched_text': matched_text,
                        'similarity': 1.0
                    })
                else:
                    # Try fuzzy matching
                    words = text.split()
                    for i in range(len(words)):
                        for j in range(i + 1, min(i + 4, len(words) + 1)):
                            phrase = ' '.join(words[i:j])
                            ratio = fuzz.ratio(entity.lower(), phrase.lower())
                            if ratio >= threshold:
                                start = text.find(phrase)
                                end = start + len(phrase)
                                matched_text = text[start:end]
                                print(f"Found fuzzy match for '{entity}' with ratio {ratio}")
                                print(f"Matched text: '{matched_text}'")
                                matches.append({
                                    'entity': entity,
                                    'start': start,
                                    'end': end,
                                    'matched_text': matched_text,
                                    'similarity': ratio / 100.0  # Convert to 0-1 scale
                                })
        
        print(f"\nFinal matches found: {matches}")
        return matches
    except Exception as e:
        print(f"Error in get_semantic_matches: {str(e)}")
        import traceback
        traceback.print_exc()
        return []

@app.route('/get_text/<int:text_id>')
def get_text(text_id):
    record = TextIndex.query.get(text_id)
    if not record:
        return jsonify({'error': 'Text not found'}), 404

    entities = []
    with open("database.jsonl", "r") as f:
        for line in f:
            data = json.loads(line)
            if data.get("text_id") == record.text_id:
                for k, v in data.items():
                    if k not in ["text", "text_id"]:
                        entities.extend(v)

    # Format the text before sending
    formatted_text = format_text_for_display(record.text)
    print(f"Original text: {record.text}")
    print(f"Formatted text: {formatted_text}")

    # Return both the formatted text and entities
    return jsonify({
        "text": formatted_text,
        "entities": entities
    })

@app.route('/get_categories/<string:text_id>')
def get_categories(text_id):
    text_record = TextIndex.query.get_or_404(text_id)
    with open('database.jsonl', 'r') as f:
        for line in f:
            record = json.loads(line)
            if record.get("text_id") == text_record.text_id:
                categories = [k for k in record.keys() if k not in ["text", "text_id"]]
                result_categories = []
                for category in categories:
                    match_result = MatchResult.query.filter_by(
                        user_id=session['user_id'],
                        text_id=text_record.id,
                        category=category
                    ).first()
                    result_categories.append({
                        'name': category,
                        'done': match_result is not None
                    })
                return jsonify({'categories': result_categories})
    return jsonify({'categories': []})

@app.route('/get_entities/<string:text_id>/<category>')
def get_entities(text_id, category):
    try:
        print(f"\nGetting entities for text_id: {text_id}, category: {category}")
        
        # Get the text record for the specific text_id
        text_record = TextIndex.query.filter_by(text_id=text_id).first()
        if not text_record:
            return jsonify({'error': 'Text not found'}), 404
            
        print(f"Found text: {text_record.text}")
        
        # Get matching method from query parameters
        method = request.args.get('method', 'sentence')
        
        # Only process entities for the current text_id and category
        with open('database.jsonl', 'r') as f:
            for line in f:
                record = json.loads(line)
                if record.get("text_id") == text_id and category in record:
                    entities = record.get(category, [])
                    print(f"Found entities for category {category}: {entities}")
                    
                    # Get matches only for the current text and category
                    matches = get_semantic_matches(text_record.text, entities, method=method)
                    print(f"Returning matches for text_id {text_id} and category {category}: {matches}")
                    
                    return jsonify({
                        'entities': entities,
                        'matches': matches
                    })
        
        # If no matching record found
        return jsonify({'entities': [], 'matches': []})
        
    except Exception as e:
        print(f"Error in get_entities: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    all_records = load_all_records_from_jsonl()
    annotated = MatchResult.query.filter_by(user_id=session['user_id']).all()
    annotated_map = {(r.text.text_id, r.category) for r in annotated}

    texts = TextIndex.query.all()
    text_status = []

    for text_obj in texts:
        related_records = [r for r in all_records if r['text_id'] == text_obj.text_id]
        all_categories = list(set(r['category'] for r in related_records))
        remaining = [cat for cat in all_categories if (text_obj.text_id, cat) not in annotated_map]
        is_annotated = len(remaining) == 0
        text_status.append({
            'text_id': text_obj.text_id,
            'text': text_obj.text,
            'is_annotated': is_annotated
        })

    return render_template('index.html', text_status=text_status)

@app.route('/save', methods=['POST'])
def save():
    if 'user_id' not in session:
        return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401

    try:
        data = request.get_json()
        if not data:
            return jsonify({'status': 'error', 'message': 'No data provided'}), 400

        text = data.get('text', '')
        entities_dict = data.get('entities', {})
        matched_dict = data.get('matched', {})
        unmatched_dict = data.get('unmatched', {})
        undetected_entity_dict = data.get('undetected_entity', {})
        text_id = data.get('text_id', '')

        if not text_id:
            return jsonify({'status': 'error', 'message': 'text_id is required'}), 400

        if not all(isinstance(d, dict) for d in [entities_dict, matched_dict, unmatched_dict, undetected_entity_dict]):
            return jsonify({'status': 'error', 'message': 'Invalid data format'}), 400

        text_record = TextIndex.query.filter_by(text_id=text_id).first()
        if not text_record:
            text_record = TextIndex(text=text, text_id=text_id)
            db.session.add(text_record)
            db.session.commit()

        for category, entity_list in entities_dict.items():
            if not isinstance(entity_list, list):
                continue

            # Check if this category has already been annotated
            existing = MatchResult.query.filter_by(
                user_id=session['user_id'],
                text_id=text_record.id,
                category=category
            ).first()

            if existing:
                continue

            result = MatchResult(
                text_id=text_record.id,
                category=category,
                entities=", ".join(entity_list),
                matched=", ".join(matched_dict.get(category, [])),
                unmatched=", ".join(unmatched_dict.get(category, [])),
                undetected_entity=", ".join(undetected_entity_dict.get(category, [])),
                user_id=session['user_id']
            )
            db.session.add(result)

        db.session.commit()
        return jsonify({'status': 'success'})

    except Exception as e:
        db.session.rollback()
        print(f"Error in save endpoint: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/review')
def review():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    results = MatchResult.query.options(joinedload(MatchResult.text)).filter_by(user_id=session['user_id']).all()
    return render_template('review.html', results=results)

@app.route('/delete/<int:record_id>', methods=['POST'])
def delete_record(record_id):
    try:
        if 'user_id' not in session:
            return jsonify({'status': 'error', 'message': 'Not authenticated'}), 401

        record = MatchResult.query.get_or_404(record_id)
        if record.user_id != session['user_id']:
            return jsonify({'status': 'error', 'message': 'Not authorized to delete this record'}), 403

        db.session.delete(record)
        db.session.commit()
        print(f"Successfully deleted record {record_id}")  # Debug log
        return jsonify({'status': 'success', 'message': 'Record deleted successfully'})
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting record {record_id}: {str(e)}")  # Debug log
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        user = User.query.get(session['user_id'])

        if not check_password_hash(user.password, current_password):
            flash('Current password is incorrect.', 'danger')
        elif new_password != confirm_password:
            flash('New passwords do not match.', 'warning')
        else:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            flash('Password updated successfully. Please log in again.', 'success')
            session.pop('user_id', None)
            return redirect(url_for('login'))

    return render_template('change_password.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.first():
            db.session.add(User(username='admin', password=generate_password_hash('admin')))
            db.session.commit()
    app.run(debug=True)
