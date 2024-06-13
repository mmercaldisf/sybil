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
        print("Usage: python gsheets_importer.py <csv_import_path>")
        sys.exit(1)
    
    csv_import_path = sys.argv[1]
    db = db_manager.DBManager(config.DATABASE_URL)
    with open(csv_import_path) as csvfile:
        reader = csv.DictReader(csvfile,delimiter='\t')
        approved_count = 0
        rejected_count = 0

        for row in reader:
            db_entry = db.get_learning_entry_by_id(row['Sources'])
            if not db_entry:
                continue
            item_state = row['State'].upper()
            if db_entry.state == item_state:
                continue
            # TODO: Only Update if the verdict has changed.
            if item_state == "APPROVED":
                db.update_learning_by_conversation_id(row['Sources'],state="APPROVED")
                approved_count +=1
            elif item_state == "REJECTED":
                db.update_learning_by_conversation_id(row['Sources'],state="REJECTED")
                rejected_count +=1
            else:
                pass

        print("Import Complete!")
        print(f"Approved: {approved_count} Rejected: {rejected_count}")
