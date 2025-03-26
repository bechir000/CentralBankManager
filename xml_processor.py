import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import logging
from app import db
from models import (MM320T_SOUM_ACCORDE2106_Int, MM110T_OPM_JOUR2106_Int, 
                   MM319T_SOUM_BQ2106_Int, MM334T_SOUM_BQ2106_Int)

logger = logging.getLogger(__name__)

def convert_date(date_str):
    """Convert YYYYMMDD format to Python date object"""
    try:
        if len(date_str) == 8:  # format YYYYMMDD
            return datetime.strptime(date_str, "%Y%m%d").date()
        else:
            # Try other common date formats
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            raise ValueError(f"Unable to parse date: {date_str}")
    except Exception as e:
        logger.error(f"Error converting date {date_str}: {str(e)}")
        raise

def find_xml_element(root, xpath):
    """Helper function to find XML elements, with error handling"""
    try:
        element = root.find(xpath)
        if element is not None:
            return element.text
        return None
    except Exception as e:
        logger.error(f"Error finding XML element at {xpath}: {str(e)}")
        return None

def validate_xml_structure(xml_file):
    """Validate that the XML file has the expected structure"""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        # Check for required elements
        required_elements = [
            ".//mm_deal",
            ".//value_date",
            ".//maturity_date"
        ]
        
        for element in required_elements:
            if root.find(element) is None:
                raise ValueError(f"Missing required element: {element}")
                
        return True, "XML structure is valid"
    except Exception as e:
        logger.error(f"XML validation error: {str(e)}")
        return False, f"XML validation error: {str(e)}"

def process_xml_file(xml_file_path, xml_file_id):
    """Process an XML file and insert data into intermediate tables"""
    # First validate the XML structure
    valid, message = validate_xml_structure(xml_file_path)
    if not valid:
        raise ValueError(message)
    
    # Parse the XML file
    tree = ET.parse(xml_file_path)
    root = tree.getroot()
    
    # Process each mm_deal element in the XML
    for deal_idx, deal in enumerate(root.findall(".//mm_deal")):
        process_deal(deal, deal_idx, xml_file_id)
    
    db.session.commit()
    logger.info(f"Successfully processed XML file {xml_file_path}")

def process_deal(deal, deal_idx, xml_file_id):
    """Process a single mm_deal element from the XML"""
    try:
        # Extract common values
        value_date_str = find_xml_element(deal, ".//value_date")
        maturity_date_str = find_xml_element(deal, ".//maturity_date")
        
        if not value_date_str or not maturity_date_str:
            raise ValueError("Missing required date fields")
            
        value_date = convert_date(value_date_str)
        maturity_date = convert_date(maturity_date_str)
        
        # Calculate duration
        duration = (maturity_date - value_date).days
        
        # Date of maturity minus 1 day for DATE_ECH
        date_ech = maturity_date - timedelta(days=1)
        
        # Get maker_id and taker_id
        maker_id = find_xml_element(deal, ".//maker_id") or "00"
        taker_id = find_xml_element(deal, ".//taker_id")
        
        if not taker_id:
            raise ValueError("Missing taker_id (RECEVEUR)")
            
        # Get amount and rate
        amount = None
        rate = None
        
        for leg in deal.findall(".//leg"):
            amount_elem = leg.find(".//amount")
            if amount_elem is not None:
                amount = float(amount_elem.text)
                
            quote = leg.find(".//quote")
            if quote is not None:
                all_in = quote.find(".//all_in")
                if all_in is not None:
                    rate = float(all_in.text)
        
        if amount is None or rate is None:
            raise ValueError("Missing amount or rate information")
        
        # Create a NUM_OPER value (increment for each deal)
        num_oper = str((deal_idx % 9) + 1)  # Generate values 1-9 as string
        
        # Create common record data
        common_data = {
            "DATE_OPER": value_date,
            "CODE_OPER": 70,
            "DONNEUR": maker_id,
            "RECEVEUR": taker_id,
            "NUM_OPER": num_oper,
            "MONT": amount,
            "TAUX": rate,
            "DUREE": duration,
            "DATE_ECH": date_ech,
            "TYPE_PLACE": "TERME",
            "DATE_REGL": maturity_date,
            "FLAGCPT_ADMIS": " ",
            "FLAGCPT_TOMBE": " ",
            "NBRBON": None,
            "ETAT_OPER": "V",
            "NUM_OPER_GESTION": None,
            "UTILISATEUR": None,
            "DATE_SAISIE": datetime.now().date(),
            "ACCEP_CP": None,
            "CODE_ISIN": "N",
            "xml_file_id": xml_file_id
        }
        
        # Create records in all 4 intermediate tables
        mm320t_record = MM320T_SOUM_ACCORDE2106_Int(**common_data)
        mm110t_record = MM110T_OPM_JOUR2106_Int(**common_data)
        
        # For MM319T and MM334T, set DONNEUR to '00'
        mm319t_data = common_data.copy()
        mm319t_data["DONNEUR"] = "00"
        mm319t_record = MM319T_SOUM_BQ2106_Int(**mm319t_data)
        
        mm334t_data = common_data.copy()
        mm334t_data["DONNEUR"] = "00"
        mm334t_record = MM334T_SOUM_BQ2106_Int(**mm334t_data)
        
        # Add to database
        db.session.add(mm320t_record)
        db.session.add(mm110t_record)
        db.session.add(mm319t_record)
        db.session.add(mm334t_record)
        
    except Exception as e:
        logger.error(f"Error processing deal: {str(e)}")
        db.session.rollback()
        raise
