import os
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "dataset", "spam.csv")
MODEL_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODEL_DIR, "spam_model.pkl")

os.makedirs(MODEL_DIR, exist_ok=True)


print("Loading dataset...")

df = pd.read_csv(DATASET_PATH, encoding="latin-1")

print("Dataset columns:", df.columns.tolist())

# Keep only useful columns
df = df.iloc[:, :2]
df.columns = ["label", "message"]

# Remove missing values
df.dropna(inplace=True)

# Remove duplicates
df.drop_duplicates(inplace=True)

# Convert labels
df["label"] = df["label"].str.lower().map({
    "ham": 0,
    "spam": 1
})

# Remove invalid rows
df.dropna(inplace=True)

X = df["message"]
y = df["label"]

print("Total messages:", len(df))
print("Spam messages:", int(y.sum()))
print("Ham messages:", int(len(y) - y.sum()))


# Split dataset
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


# Create ML Pipeline
model = Pipeline([
    (
        "tfidf",
        TfidfVectorizer(
            stop_words="english",
            lowercase=True,
            max_features=10000,
            ngram_range=(1, 2)
        )
    ),
    (
        "classifier",
        MultinomialNB()
    )
])


print("\nTraining model...")

model.fit(X_train, y_train)


# Predictions
predictions = model.predict(X_test)

accuracy = accuracy_score(y_test, predictions)

print("\n========== MODEL RESULTS ==========")
print(f"Accuracy: {accuracy * 100:.2f}%")

print("\nClassification Report:")
print(classification_report(
    y_test,
    predictions,
    target_names=["Ham", "Spam"]
))


# Save model
joblib.dump(model, MODEL_PATH)

print("\nModel saved successfully!")
print("Location:", MODEL_PATH)