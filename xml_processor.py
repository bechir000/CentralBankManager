from lxml import etree as ET
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
        
        # Check for required elements for deposit deal
        if root.find(".//mm_deal") is None:
            raise ValueError("Missing required element: mm_deal")
        
        # Check for leg element
        if root.find(".//leg") is None:
            raise ValueError("Missing required element: leg")
            
        # Check for value_date in the first leg
        if root.find(".//leg/value_date") is None:
            raise ValueError("Missing required element: value_date")
            
        # Check for maturity_date in the first leg
        if root.find(".//leg/maturity_date") is None:
            raise ValueError("Missing required element: maturity_date")
                
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
        # Get the root element (parent of mm_deal)
        root = deal.getparent()
        
        # Extract maker_id from the XML structure
        maker_id_elem = root.find(".//maker_id")
        maker_id = maker_id_elem.text if maker_id_elem is not None else "00"
        
        # Truncate maker_id to 2 characters if needed
        if len(maker_id) > 2:
            maker_id = maker_id[:2]
        
        # Extract taker_id from the XML structure
        taker_id_elem = root.find(".//taker_id")
        taker_id = taker_id_elem.text if taker_id_elem is not None else None
        
        if not taker_id:
            # Fall back to sub_party id if available
            taker_party = root.find(".//party[@role='COUNTERPARTY'][@related_to='TAKER']")
            if taker_party is not None:
                taker_sub_party = taker_party.find(".//sub_party[@role='EXECUTING_TRADER']")
                if taker_sub_party is not None:
                    taker_id_elem = taker_sub_party.find(".//sub_party_id[@name='ID']")
                    if taker_id_elem is not None:
                        taker_id = taker_id_elem.text
        
        if not taker_id or taker_id == "#UNSPECIFIED#":
            # Use a default value if not found
            taker_id = "01"
            
        # Truncate taker_id to 2 characters if needed
        if len(taker_id) > 2:
            taker_id = taker_id[:2]
        
        # Find the first leg element
        leg = deal.find(".//leg")
        if leg is None:
            raise ValueError("No leg element found in the deal")
        
        # Extract dates from the leg
        value_date_elem = leg.find(".//value_date")
        maturity_date_elem = leg.find(".//maturity_date")
        
        if value_date_elem is None or maturity_date_elem is None:
            raise ValueError("Missing required date fields in the leg")
            
        value_date_str = value_date_elem.text
        maturity_date_str = maturity_date_elem.text
        
        value_date = convert_date(value_date_str)
        maturity_date = convert_date(maturity_date_str)
        
        # Calculate duration
        duration = (maturity_date - value_date).days
        
        # Date of maturity minus 1 day for DATE_ECH
        date_ech = maturity_date - timedelta(days=1)
        
        # Get amount and rate from the leg
        amount_elem = leg.find(".//amount")
        amount = float(amount_elem.text) if amount_elem is not None else None
        
        rate = None
        quote_elem = leg.find(".//quote")
        if quote_elem is not None:
            all_in_elem = quote_elem.find(".//all_in")
            if all_in_elem is not None:
                rate = float(all_in_elem.text)
        
        if amount is None or rate is None:
            raise ValueError("Missing amount or rate information in the leg")
        
        # Create a NUM_OPER value (increment for each deal)
        num_oper = str((deal_idx % 9) + 1)  # Generate values 1-9 as string
        
        # Extract deal_date if available
        deal_date_elem = root.find(".//deal_date")
        deal_date = None
        if deal_date_elem is not None:
            try:
                deal_date = convert_date(deal_date_elem.text)
            except:
                deal_date = datetime.now().date()
        else:
            deal_date = datetime.now().date()
        
        # Create common record data
        common_data = {
            "DATE_OPER": deal_date,
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
        
        # Logging for debugging
        logger.info(f"Processed deal with data: maker_id={maker_id}, taker_id={taker_id}, amount={amount}, rate={rate}")
        
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
