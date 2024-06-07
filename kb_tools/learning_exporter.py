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
        print("Usage: python learning_exporter.py <csv_export_path>")
        sys.exit(1)
    
    csv_export_path = sys.argv[1]
    db = db_manager.DBManager(config.DATABASE_URL)
    learning = db.get_learning_entries_with_state("READY")
    with open(csv_export_path, mode='w') as csvfile:
        fieldnames = ['Evaluation','Question', 'Answer', 'Nuance', 'Sources']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for entry in learning:
            
            writer.writerow({'Evaluation':entry.evaluation,'Question': entry.question, 'Answer': entry.answer, 'Nuance': entry.nuance, 'Sources': entry.conversation_id})

    print(f"Learning Export Complete: Imported {len(learning)} entries.")