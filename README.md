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
├── app.py                    # Main application file
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (create this file)
├── database.jsonl            # Sample data file for import
├── instance/                 # Auto-generated instance folder
│   └── entities.db           # SQLite database (created automatically)
└── templates/                # HTML templates
    ├── index.html            # Main annotation interface
    ├── login.html            # Login page
    ├── review.html           # Annotation review page
    ├── change_password.html  # Password change page
    └── import_database.html  # Database import interface
```

## Troubleshooting

1. **Database Issues**
   - If you encounter database errors, check the `instance` directory for `entities.db`
   - If needed, delete the `entities.db` file and restart the application to recreate it
   - Make sure your `.env` file contains the correct `DATABASE_URI` setting

2. **Package Installation Issues**
   - Make sure you're using Python 3.8 or higher: `python --version`
   - Try updating pip: `python -m pip install --upgrade pip`
   - If you get errors with sentence-transformers, ensure you have sufficient storage space (the model is large)
   - For Windows users, you might need to install Visual C++ Build Tools for some packages

3. **Model Download Issues**
   - The first run might take longer as it downloads the S-PubMedBert-MS-MARCO model
   - Ensure you have a stable internet connection
   - Temporary download issues can usually be resolved by restarting the application
   - If the model fails to download, check your firewall or proxy settings

4. **Import Issues**
   - The database import expects a specific JSONL format as shown in the `database.jsonl` file
   - Each record must contain at least `text_id`, `text`, and one category field
   - The application will validate the import and show error messages for invalid records

## Security Notes

1. **Authentication**
   - Change the default admin password immediately after first login
   - Use a strong, unique password for your account
   - The application stores password hashes, not actual passwords

2. **Configuration**
   - Keep your `.env` file secure and never commit it to version control
   - Use a strong, random `SECRET_KEY` (at least a 16-character random string)
   - For production, consider using environment variables instead of an `.env` file

3. **Production Deployment**
   - The default setup is for development only
   - For production:
     * Use a proper WSGI server (Gunicorn, uWSGI) instead of the Flask development server
     * Configure HTTPS with a valid certificate
     * Use a more robust database (PostgreSQL, MySQL) instead of SQLite
     * Implement proper logging and monitoring
     * Consider using a web server like Nginx or Apache as a reverse proxy

4. **Data Privacy**
   - Be mindful of the clinical data you store in the application
   - Ensure you have appropriate permissions to use any clinical text
   - Consider anonymizing sensitive clinical information before import

## Support

For issues or questions, please open an issue in the repository or contact the development team. 
