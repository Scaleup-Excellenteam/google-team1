import sqlite3
import os
import re
import string


def normalize_text(text: str) -> str:
    """
    Normalizes a string by converting it to lowercase, removing all punctuation, and handling multiple spaces.
    """
    # Create a translation table to remove all punctuation
    translator = str.maketrans('', '', string.punctuation)
    text = text.translate(translator)

    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def initialize_database(root_folder: str):
    """
        Initializes the SQLite database and populates it with sentences from text files.
        """
    conn = sqlite3.connect('autocomplete.db')
    cursor = conn.cursor()

    cursor.execute('''
            CREATE TABLE IF NOT EXISTS sentences (
                id INTEGER PRIMARY KEY,
                sentence TEXT,
                normalized_sentence TEXT,
                source_file TEXT,
                line_offset INTEGER
            )
        ''')
    conn.commit()

    total_sentences = 0
    for dirpath, _, filenames in os.walk(root_folder):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        sentence = line.strip()
                        if sentence:
                            normalized_sentence = normalize_text(sentence)
                            cursor.execute(
                                "INSERT INTO sentences (sentence, normalized_sentence, source_file, line_offset) VALUES (?, ?, ?, ?)",
                                (sentence, normalized_sentence, file_path, i + 1)
                            )
                            total_sentences += 1
            except Exception as e:
                print(f"Could not read file {file_path}: {e}")
    conn.commit()
    conn.close()
    print("Loading the files and preparing the system...")
    print(f"The system is ready. Loaded {total_sentences} sentences.")

