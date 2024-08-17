import pandas as pd
import os
import pickle
import logging
import sqlite3
from Levenshtein import distance as levenshtein_distance

# Paths to the metadata file, the directory containing book files, the SQLite database, and the checkpoint file
metadata_file_path = '/Users/puter/Downloads/archive/gutenberg_over_70000_metadata.csv'
book_directory_path = '/Users/puter/Downloads/archive'
database_path = '/Users/puter/Desktop/quotes_cleaned.db'
checkpoint_file_path = '/Users/puter/Desktop/checkpoint.txt'

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Load metadata
metadata = pd.read_csv(metadata_file_path)

# Display the first few rows of the metadata to understand its structure
logging.debug(metadata.head())

# Standardize author names in the metadata (Last, First to First Last)
def standardize_author_name(author):
    parts = author.split(',')
    if len(parts) == 2:
        return parts[1].strip() + ' ' + parts[0].strip()
    return author.strip()

metadata['Author'] = metadata['Author'].apply(standardize_author_name)

# Display the unique author names to inspect their format
unique_authors = metadata['Author'].unique()
logging.debug(f"Unique authors: {unique_authors}")

# Filter metadata to include only relevant columns
metadata = metadata[['Book Num', 'Book Title', 'Author']]

def load_pickle_file(file_path):
    """Load a pickle file and return its content."""
    try:
        with open(file_path, 'rb') as file:
            data = pickle.load(file)
        return data
    except Exception as e:
        logging.error(f"Failed to load {file_path}: {e}")
        return None

def normalize_text(text):
    """Normalize text by removing non-alphanumeric characters but preserving spaces and basic punctuation."""
    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 ,.?!;:'\"-")
    return ''.join(c if c in allowed_chars else ' ' for c in text)

def find_sentence_boundary(text, index, direction):
    """Find the nearest sentence boundary (., ?, !) in the specified direction."""
    while 0 <= index < len(text):
        if text[index] in '.!?':
            return index + 1 if direction == 'right' else index
        index += 1 if direction == 'right' else -1
    return index

def search_quote_in_text(book_text, quote):
    """Search for a quote in the book text using Levenshtein distance."""
    normalized_book_text = normalize_text(book_text.lower())
    normalized_quote = normalize_text(quote.lower())

    # Log the normalized texts for debugging
    logging.debug(f"Normalized Book Text: {normalized_book_text[:1000]}")
    logging.debug(f"Normalized Quote: {normalized_quote}")

    min_distance = float('inf')
    best_match_start = -1
    best_match_end = -1

    # Sliding window approach to find the closest match
    for start_idx in range(len(normalized_book_text) - len(normalized_quote) + 1):
        window_text = normalized_book_text[start_idx:start_idx + len(normalized_quote)]
        distance = levenshtein_distance(window_text, normalized_quote)
        if distance < min_distance:
            min_distance = distance
            best_match_start = start_idx
            best_match_end = start_idx + len(normalized_quote)

    if min_distance <= len(normalized_quote) * 0.2:  # Allow up to 20% of the quote length as differences
        context_start = max(0, best_match_start - 1000)
        context_end = min(len(normalized_book_text), best_match_end + 1000)

        # Adjust context to stop at sentence boundaries
        context_start = find_sentence_boundary(normalized_book_text, context_start, 'left')
        context_end = find_sentence_boundary(normalized_book_text, context_end, 'right')

        context = book_text[context_start:context_end]
        return best_match_start, context
    return None, None

def process_quote(quote_id, quote, author):
    """Process a single quote."""
    # Filter books by the author
    author_books = metadata[metadata['Author'].str.contains(author, case=False, na=False)]

    # Log the filtered books for debugging
    logging.debug(f"Filtered books for author {author}: {author_books}")

    if author_books.empty:
        logging.info(f"No books found for author: {author}")
        return None

    found_context = None
    for index, row in author_books.iterrows():
        book_num = row['Book Num']
        book_title = row['Book Title']
        logging.info(f"Checking book: {book_title} (Book Number: {book_num})")

        # Search for the book in all subdirectories
        processed_files = 0
        for root, dirs, files in os.walk(book_directory_path):
            for file in files:
                if file.startswith(str(book_num)) and file.endswith('.pkl'):
                    pickle_file_path = os.path.join(root, file)
                    logging.debug(f"Found file: {pickle_file_path}")

                    # Load and search the pickle file
                    book_text = load_pickle_file(pickle_file_path)
                    if book_text is not None:
                        word_index, context = search_quote_in_text(book_text, quote)
                        if word_index is not None:
                            logging.info(
                                f"Quote found in the book '{book_title}' (Book Number: {book_num}), at word index: {word_index}")
                            found_context = context
                            break
                    processed_files += 1
                    if processed_files >= 5:  # Limit to processing 5 files per book to avoid long runtime
                        break
            if found_context:
                break
        if found_context:
            break

    if not found_context:
        logging.info(f"Quote not found in any of the books by {author}")
    return found_context

def update_quote_context_in_db(quote_id, context):
    """Update the context of a quote in the database."""
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("UPDATE quotes_cleaned SET context = ? WHERE id = ?", (context, quote_id))
    conn.commit()
    conn.close()

def save_checkpoint(quote_id):
    """Save the current quote ID to the checkpoint file."""
    with open(checkpoint_file_path, 'w') as file:
        file.write(str(quote_id))

def load_checkpoint():
    """Load the last processed quote ID from the checkpoint file."""
    if os.path.exists(checkpoint_file_path):
        with open(checkpoint_file_path, 'r') as file:
            return int(file.read().strip())
    return None

def main():
    """Main function to process quotes."""
    last_processed_id = load_checkpoint()
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    if last_processed_id:
        cursor.execute("SELECT id, quote, author FROM quotes_cleaned WHERE context IS NULL AND id > ? ORDER BY id", (last_processed_id,))
    else:
        cursor.execute("SELECT id, quote, author FROM quotes_cleaned WHERE context IS NULL ORDER BY id")
    quotes = cursor.fetchall()
    conn.close()

    for quote_info in quotes:
        quote_id, quote, author = quote_info
        logging.info(f"Processing quote: '{quote}' by {author} (ID: {quote_id})")
        context = process_quote(quote_id, quote, author)
        if context:
            update_quote_context_in_db(quote_id, context)
            logging.info(f"Updated context for Quote ID: {quote_id}")
        save_checkpoint(quote_id)  # Save the checkpoint after processing each quote

if __name__ == "__main__":
    main()
