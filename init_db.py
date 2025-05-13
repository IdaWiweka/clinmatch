from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///entities.db'
db = SQLAlchemy(app)

# Models
class TextIndex(db.Model):
    text_id = db.Column(db.String, primary_key=True)  # Primary key must be set
    text = db.Column(db.Text, nullable=False)
    __table_args__ = (
        db.UniqueConstraint('text_id', 'text', name='unique_text_id'),
    )


# Load records function
def load_all_records_from_jsonl():
    import json
    records = []
    with open("database.jsonl", "r", encoding="utf-8") as f:
        for line in f:
            records.append(json.loads(line))
    return records

# Initialize only once
def initialize_texts_once():
    if TextIndex.query.first():  # Already initialized
        return
    records = load_all_records_from_jsonl()
    
    # Build set of new unique (text_id, text) pairs
    existing_pairs = {(t.text_id, t.text) for t in TextIndex.query.all()}
    new_records = [
        TextIndex(text_id=record['text_id'], text=record['text'])
        for record in records
        if (record['text_id'], record['text']) not in existing_pairs
    ]
    
    db.session.add_all(new_records)
    db.session.commit()
    print(f"✅ Initialized {len(new_records)} new text records.")

# Manual init route
@app.route('/init_texts')
def init_texts_route():
    initialize_texts_once()
    return "Texts initialized."

# Run app
if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # Ensure tables exist
        initialize_texts_once()
    app.run(debug=True)
