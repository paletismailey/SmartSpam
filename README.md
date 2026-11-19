# SmartSpam: Intelligent Email Spam Detection

A beginner-friendly machine learning project that classifies text as SPAM or HAM using NLP, TF-IDF and Multinomial Naive Bayes.

## Technologies
- Python
- Pandas
- NLTK
- Scikit-learn
- TF-IDF
- Multinomial Naive Bayes
- Flask
- HTML/CSS

## Project Structure

SmartSpam/
- dataset/spam.csv
- model/
- templates/index.html
- static/style.css
- train_model.py
- app.py
- requirements.txt

## How to Run

1. Open the SmartSpam folder in VS Code.
2. Open a terminal.
3. Create a virtual environment:
   `py -m venv venv`
4. Activate it:
   `venv\Scripts\activate`
5. Install packages:
   `pip install -r requirements.txt`
6. Train the model:
   `python train_model.py`
7. Start the Flask app:
   `python app.py`
8. Open:
   `http://127.0.0.1:5000`

## Important
The included CSV is a small demonstration dataset so the project can be tested immediately. For a college-level final model, replace it with a larger standard spam dataset and retrain the model.
