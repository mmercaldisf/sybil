# Exports the knowledgebase to a CSV file
import os
import sys
import csv 

# Some modules are in the parent directory. Make sure to add the path to sys.path if needed
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
import config
import db_manager


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python knowledgebase_exporter.py <csv_export_path>")
        sys.exit(1)
    
    csv_export_path = sys.argv[1]
    db = db_manager.DBManager(config.DATABASE_URL)
    knowledgebase = db.get_all_knowledge()
    with open(csv_export_path, mode='w') as csvfile:
        fieldnames = ['Question', 'Answer', 'Nuance', 'Sources']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for knowledge in knowledgebase:
            
            writer.writerow({'Question': knowledge.question, 'Answer': knowledge.answer, 'Nuance': knowledge.nuance, 'Sources': knowledge.sources})

    print(f"Knowledgebase Export Complete: Imported {len(knowledgebase)} entries.")