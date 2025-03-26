from datetime import datetime
from app import db

class BaseOperation:
    """Base class for common columns in all operation tables"""
    DATE_OPER = db.Column(db.Date, nullable=False)
    CODE_OPER = db.Column(db.Integer, nullable=False, default=70)
    DONNEUR = db.Column(db.String(2), nullable=False)
    RECEVEUR = db.Column(db.String(2), nullable=False)
    NUM_OPER = db.Column(db.String(1), nullable=False)
    MONT = db.Column(db.Numeric(15, 3), nullable=False)
    TAUX = db.Column(db.Numeric(7, 5), nullable=False)
    DUREE = db.Column(db.Integer, nullable=False)
    DATE_ECH = db.Column(db.Date, nullable=False)
    TYPE_PLACE = db.Column(db.String(5), nullable=False, default="TERME")
    DATE_REGL = db.Column(db.Date, nullable=False)
    FLAGCPT_ADMIS = db.Column(db.String(1), nullable=True)
    FLAGCPT_TOMBE = db.Column(db.String(1), nullable=True)
    NBRBON = db.Column(db.Integer, nullable=True)
    ETAT_OPER = db.Column(db.String(1), nullable=False, default="V")
    NUM_OPER_GESTION = db.Column(db.Integer, nullable=True)
    UTILISATEUR = db.Column(db.String(10), nullable=True)
    DATE_SAISIE = db.Column(db.Date, nullable=False, default=datetime.now)
    ACCEP_CP = db.Column(db.String(1), nullable=True)
    CODE_ISIN = db.Column(db.String(12), nullable=False, default="N")

# Intermediate Tables
class MM320T_SOUM_ACCORDE2106_Int(db.Model, BaseOperation):
    __tablename__ = 'mm320t_soum_accorde2106_int'
    id = db.Column(db.Integer, primary_key=True)
    validation_status = db.Column(db.String(20), default='pending')
    xml_file_id = db.Column(db.Integer, db.ForeignKey('xml_files.id'))

class MM110T_OPM_JOUR2106_Int(db.Model, BaseOperation):
    __tablename__ = 'mm110t_opm_jour2106_int'
    id = db.Column(db.Integer, primary_key=True)
    validation_status = db.Column(db.String(20), default='pending')
    xml_file_id = db.Column(db.Integer, db.ForeignKey('xml_files.id'))

class MM319T_SOUM_BQ2106_Int(db.Model, BaseOperation):
    __tablename__ = 'mm319t_soum_bq2106_int'
    id = db.Column(db.Integer, primary_key=True)
    validation_status = db.Column(db.String(20), default='pending')
    xml_file_id = db.Column(db.Integer, db.ForeignKey('xml_files.id'))

class MM334T_SOUM_BQ2106_Int(db.Model, BaseOperation):
    __tablename__ = 'mm334t_soum_bq2106_int'
    id = db.Column(db.Integer, primary_key=True)
    validation_status = db.Column(db.String(20), default='pending')
    xml_file_id = db.Column(db.Integer, db.ForeignKey('xml_files.id'))

# Final Tables
class MM320T_SOUM_ACCORDE2106_Final(db.Model, BaseOperation):
    __tablename__ = 'mm320t_soum_accorde2106_final'
    id = db.Column(db.Integer, primary_key=True)
    statut_validation = db.Column(db.String(20), default='validated')
    original_id = db.Column(db.Integer, nullable=True)
    
class MM110T_OPM_JOUR2106_Final(db.Model, BaseOperation):
    __tablename__ = 'mm110t_opm_jour2106_final'
    id = db.Column(db.Integer, primary_key=True)
    statut_validation = db.Column(db.String(20), default='validated')
    original_id = db.Column(db.Integer, nullable=True)

class MM319T_SOUM_BQ2106_Final(db.Model, BaseOperation):
    __tablename__ = 'mm319t_soum_bq2106_final'
    id = db.Column(db.Integer, primary_key=True)
    statut_validation = db.Column(db.String(20), default='validated')
    original_id = db.Column(db.Integer, nullable=True)

class MM334T_SOUM_BQ2106_Final(db.Model, BaseOperation):
    __tablename__ = 'mm334t_soum_bq2106_final'
    id = db.Column(db.Integer, primary_key=True)
    statut_validation = db.Column(db.String(20), default='validated')
    original_id = db.Column(db.Integer, nullable=True)

# XML File metadata
class XMLFile(db.Model):
    __tablename__ = 'xml_files'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    bank_name = db.Column(db.String(100), nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.now)
    status = db.Column(db.String(20), default='pending')
    
    # Define relationships with intermediate tables
    mm320t_records = db.relationship('MM320T_SOUM_ACCORDE2106_Int', backref='xml_file', lazy=True)
    mm110t_records = db.relationship('MM110T_OPM_JOUR2106_Int', backref='xml_file', lazy=True)
    mm319t_records = db.relationship('MM319T_SOUM_BQ2106_Int', backref='xml_file', lazy=True)
    mm334t_records = db.relationship('MM334T_SOUM_BQ2106_Int', backref='xml_file', lazy=True)
