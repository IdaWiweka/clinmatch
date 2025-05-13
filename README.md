# Clinical Entity Matcher

A web application for matching and annotating clinical entities in text using both semantic and fuzzy matching approaches.

## Features

- Semantic matching using S-PubMedBert-MS-MARCO model
- Fuzzy matching for text similarity
- Interactive drag-and-drop interface
- User authentication system
- Review and management of saved annotations
- Password management

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Git (optional, for cloning the repository)

## Installation

1. Clone or download this repository:
```bash
git clone <[repository-url](https://github.com/IdaWiweka/clinmatch.git)>
```

2. Create a virtual environment (recommended):
```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the root directory with the following content:
```
SECRET_KEY=your-secret-key-here
DATABASE_URI=sqlite:///entities.db
```

## Database Setup

The application uses SQLite by default. The database will be automatically created when you first run the application. The initial admin credentials are:

- Username: admin
- Password: admin

**Important**: Change the default admin password after first login for security.

## Running the Application

1. Make sure your virtual environment is activated (if using one)

2. Run the Flask application:
```bash
python app.py
```

3. Open your web browser and navigate to:
```
http://localhost:5000
```

4. Log in using the default credentials:
   - Username: admin
   - Password: admin

## Usage Guide

1. **Login**
   - Use the default admin credentials for first login
   - Change your password immediately after first login

2. **Selecting Text**
   - Choose a text from the dropdown menu
   - Select a category for annotation

3. **Matching Methods**
   - Choose between Sentence Transformer or Fuzzy Matching
   - Sentence Transformer: Better for semantic similarity
   - Fuzzy Matching: Better for exact or near-exact matches

4. **Entity Matching**
   - Drag entities to "Matched" or "Unmatched" zones
   - Add undetected entities in the text area
   - Click "Save" to store your annotations

5. **Review**
   - Access saved annotations through the "Saved Data" button
   - Review, manage, or delete previous annotations

## File Structure

```
.
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── .env               # Environment variables
├── entities.db        # SQLite database (created automatically)
├── database.jsonl     # Sample data file
└── templates/         # HTML templates
    ├── index.html     # Main interface
    ├── login.html     # Login page
    ├── review.html    # Review page
    └── change_password.html  # Password change page
```

## Troubleshooting

1. **Database Issues**
   - If you encounter database errors, delete the `entities.db` file and restart the application
   - The database will be recreated automatically

2. **Package Installation Issues**
   - Make sure you're using Python 3.8 or higher
   - Try updating pip: `python -m pip install --upgrade pip`
   - For Windows users, you might need to install Visual C++ Build Tools for some packages

3. **Model Download Issues**
   - The first run might take longer as it downloads the sentence transformer model
   - Ensure you have a stable internet connection
   - Check your firewall settings if the download fails

## Security Notes

1. Change the default admin password immediately after first login
2. Keep your `.env` file secure and never commit it to version control
3. Use a strong `SECRET_KEY` in production environments
4. Consider using a more robust database in production

## Support

For issues or questions, please open an issue in the repository or contact the development team. 
