Quote Context Finder
Project Overview
This project is a novel tool designed to automatically find and add context to quotes by searching a large corpus of public domain books. It addresses the challenge of providing rich, accurate context for isolated quotes, enhancing their value and understanding.
Features

Searches through an 80GB corpus of public domain books from Project Gutenberg
Uses Levenshtein distance algorithm for fuzzy matching of quotes
Implements efficient text search using a sliding window approach
Manages quote data using SQLite database
Processes large datasets using pandas
Includes checkpoint functionality for resuming long-running processes

Technologies Used

Python
Pandas for data manipulation
SQLite for database management
Levenshtein distance algorithm for fuzzy text matching
Pickle for efficient data storage and retrieval

Setup and Installation

Clone this repository
Install required packages:
Copypip install pandas Levenshtein

Ensure you have the following data:

Gutenberg metadata CSV file
Directory containing Gutenberg book files (pickled)
SQLite database with quotes


Usage
Run the script with the following command:
Copypython quote_context_finder.py
Note: Ensure that the file paths in the script are correctly set to your local environment.
Project Structure

quote_context_finder.py: Main script containing all the logic
gutenberg_over_70000_metadata.csv: Metadata file for Gutenberg books
quotes_cleaned.db: SQLite database containing quotes
checkpoint.txt: File to store the last processed quote ID



Contributing
Contributions, issues, and feature requests are welcome. Feel free to check issues page if you want to contribute.
