import sqlite3
import os

# Define the path for the SQLite database
DB_PATH = os.path.join(os.getcwd(), "investment_analysis.db")

# Initialize or connect to an SQLite database and create the table if it doesn't exist
def init_db():
    """
    Initialize the SQLite database and create the 'analysis_data' table if it doesn't exist.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS analysis_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                parameters TEXT NOT NULL,
                content TEXT NOT NULL
            )
        ''')
        conn.commit()
        print("Database initialized and table 'analysis_data' is ready.")
    except sqlite3.Error as e:
        print(f"Error initializing database: {e}")
    finally:
        conn.close()

# Check if the 'analysis_data' table exists
def check_table_exists():
    """
    Check if the 'analysis_data' table exists in the database.
    :return: True if the table exists, False otherwise.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT name FROM sqlite_master WHERE type='table' AND name='analysis_data';
        ''')
        result = cursor.fetchone()
        if result:
            print("Table 'analysis_data' exists.")
            return True
        else:
            print("Table 'analysis_data' does not exist.")
            return False
    except sqlite3.Error as e:
        print(f"Error checking table existence: {e}")
        return False
    finally:
        conn.close()

# Save data to SQLite
def save_to_sqlite(topic, parameters, content):
    """
    Save content related to stock analysis or investment advice to SQLite.
    :param topic: Topic for the analysis (e.g., stock symbol or investment strategy)
    :param parameters: String containing user parameters (e.g., initial capital, risk tolerance)
    :param content: Analysis or advice content to save
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO analysis_data (topic, parameters, content)
            VALUES (?, ?, ?)
        ''', (topic, parameters, content))
        conn.commit()
        print("Content saved to SQLite database.")
    except sqlite3.Error as e:
        print(f"Error saving content to SQLite: {e}")
    finally:
        conn.close()

# Retrieve data from SQLite
def retrieve_from_sqlite(topic, parameters):
    """
    Retrieve saved content from SQLite based on topic and parameters.
    :param topic: Topic for the analysis (e.g., stock symbol or investment strategy)
    :param parameters: String containing user parameters (e.g., initial capital, risk tolerance)
    :return: The saved content or a message if not found
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT content FROM analysis_data
            WHERE topic = ? AND parameters = ?
        ''', (topic, parameters))
        result = cursor.fetchone()
        if result:
            print("Content retrieved successfully.")
            return result[0]  # Return the content
        else:
            print("No content found for the given topic and parameters.")
            return "No content found for the given topic and parameters."
    except sqlite3.Error as e:
        print(f"Error retrieving content from SQLite: {e}")
        return "An error occurred while retrieving the content."
    finally:
        conn.close()

# Delete data from SQLite based on topic and parameters
def delete_from_sqlite(topic, parameters):
    """
    Delete saved content from SQLite based on topic and parameters.
    :param topic: Topic for the analysis (e.g., stock symbol or investment strategy)
    :param parameters: String containing user parameters (e.g., initial capital, risk tolerance)
    :return: Message indicating whether deletion was successful or not.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM analysis_data
            WHERE topic = ? AND parameters = ?
        ''', (topic, parameters))
        conn.commit()
        if cursor.rowcount > 0:
            print("Content deleted successfully.")
            return "Content deleted successfully."
        else:
            print("No content found to delete for the given topic and parameters.")
            return "No content found to delete for the given topic and parameters."
    except sqlite3.Error as e:
        print(f"Error deleting content from SQLite: {e}")
        return "An error occurred while deleting the content."
    finally:
        conn.close()

# Retrieve all data from the database
def retrieve_all_data():
    """
    Retrieve all saved records from the 'analysis_data' table.
    :return: List of all records, or an empty list if no data is found
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM analysis_data')
        records = cursor.fetchall()
        print("All records retrieved successfully.")
        return records
    except sqlite3.Error as e:
        print(f"Error retrieving all records: {e}")
        return []
    finally:
        conn.close()

# Update existing data in SQLite based on topic and parameters
def update_sqlite(topic, parameters, new_content):
    """
    Update existing content in the SQLite database based on topic and parameters.
    :param topic: Topic for the analysis (e.g., stock symbol or investment strategy)
    :param parameters: String containing user parameters (e.g., initial capital, risk tolerance)
    :param new_content: New content to update in the database
    :return: Message indicating whether update was successful or not.
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE analysis_data
            SET content = ?
            WHERE topic = ? AND parameters = ?
        ''', (new_content, topic, parameters))
        conn.commit()
        if cursor.rowcount > 0:
            print("Content updated successfully.")
            return "Content updated successfully."
        else:
            print("No matching content found to update.")
            return "No matching content found to update."
    except sqlite3.Error as e:
        print(f"Error updating content in SQLite: {e}")
        return "An error occurred while updating the content."
    finally:
        conn.close()