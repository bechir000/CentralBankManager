import os
from app import app, db
from models import XMLFile
from xml_processor import process_xml_file

def test_processing():
    """Test the XML processor with a sample file"""
    with app.app_context():
        # Create a test XML file record
        xml_file = XMLFile(filename="MM.DEPOSIT_EXAMPLE_MAKER_2025.xml", status="pending")
        db.session.add(xml_file)
        db.session.commit()
        
        try:
            # Process the sample XML file
            xml_file_path = "uploads/MM.DEPOSIT_EXAMPLE_MAKER_2025.xml"
            if not os.path.exists(xml_file_path):
                print(f"Error: File not found at {xml_file_path}")
                return
            
            process_xml_file(xml_file_path, xml_file.id)
            print("Successfully processed XML file!")
            
            # Check if records were created
            from models import MM320T_SOUM_ACCORDE2106_Int
            records = MM320T_SOUM_ACCORDE2106_Int.query.filter_by(xml_file_id=xml_file.id).all()
            print(f"Number of MM320T records created: {len(records)}")
            
            if records:
                # Display some data from the first record
                record = records[0]
                print(f"First record data:")
                print(f"  DATE_OPER: {record.DATE_OPER}")
                print(f"  DONNEUR: {record.DONNEUR}")
                print(f"  RECEVEUR: {record.RECEVEUR}")
                print(f"  MONT: {record.MONT}")
                print(f"  TAUX: {record.TAUX}")
                print(f"  DUREE: {record.DUREE}")
        
        except Exception as e:
            print(f"Error processing XML: {str(e)}")
            db.session.rollback()

if __name__ == "__main__":
    test_processing()