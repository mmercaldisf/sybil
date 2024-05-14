# Imports a CSV file of Q&A into the knowledgebase
import os
import sys
import csv

# Some modules are in the parent directory. Make sure to add the path to sys.path if needed
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import config
import db_manager



if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python knowledgebase_importer.py <csv_import_path>")
        sys.exit(1)
    
    csv_import_path = sys.argv[1]
    db = db_manager.DBManager(config.DATABASE_URL)
    with open(csv_import_path) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            db.add_knowledge(row['Question'], row['Answer'], row['Nuance'],row['Sources'])
    print(f"Knowledgebase Import Complete: Imported {reader.line_num} entries.")