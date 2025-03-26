import os
import uuid
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import app, db
from models import (XMLFile, MM320T_SOUM_ACCORDE2106_Int, MM110T_OPM_JOUR2106_Int, 
                   MM319T_SOUM_BQ2106_Int, MM334T_SOUM_BQ2106_Int, 
                   MM320T_SOUM_ACCORDE2106_Final, MM110T_OPM_JOUR2106_Final,
                   MM319T_SOUM_BQ2106_Final, MM334T_SOUM_BQ2106_Final)
from xml_processor import process_xml_file
from forms import UploadForm

# Allowed file extensions
ALLOWED_EXTENSIONS = {'xml'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    # Get count of pending and validated files
    pending_files = XMLFile.query.filter_by(status='pending').count()
    validated_files = XMLFile.query.filter_by(status='validated').count()
    
    # Get recent uploads
    recent_uploads = XMLFile.query.order_by(XMLFile.upload_date.desc()).limit(5).all()
    
    return render_template('index.html', 
                          pending_files=pending_files, 
                          validated_files=validated_files, 
                          recent_uploads=recent_uploads)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    # Check if user is logged in
    if not current_user.is_authenticated:
        flash('You must be logged in to upload files', 'danger')
        return redirect(url_for('login'))
        
    form = UploadForm()
    if form.validate_on_submit():
        # Check if the post request has the file part
        file = form.xml_file.data
        bank_name = form.bank_name.data
        
        if file and allowed_file(file.filename):
            # Secure the filename and save it to a temporary location
            filename = secure_filename(file.filename)
            temp_path = os.path.join('/tmp', f"{uuid.uuid4()}_{filename}")
            file.save(temp_path)
            
            try:
                # Create a new XMLFile record with bank name and current user
                xml_file = XMLFile(
                    filename=filename, 
                    bank_name=bank_name, 
                    status='pending',
                    user_id=current_user.id
                )
                db.session.add(xml_file)
                db.session.commit()
                
                # Process the XML file and extract data
                process_xml_file(temp_path, xml_file.id)
                
                flash(f'Successfully uploaded and processed {filename} for {bank_name}.', 'success')
            except Exception as e:
                db.session.rollback()
                app.logger.error(f"Error processing file {filename}: {str(e)}")
                flash(f"Error processing file {filename}: {str(e)}", 'danger')
            
            # Remove the temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
        else:
            flash(f'File {file.filename} is not allowed. Only XML files are permitted.', 'danger')
            
        return redirect(url_for('index'))
    
    return render_template('upload.html', form=form)

@app.route('/validate')
@login_required
def validate():
    # Check if user is admin
    if not current_user.has_role('admin'):
        flash('Only administrators can validate files', 'danger')
        return redirect(url_for('index'))
        
    # Get all pending XML files
    pending_files = XMLFile.query.filter_by(status='pending').all()
    return render_template('validate.html', pending_files=pending_files)

@app.route('/review/<int:file_id>')
@login_required
def review(file_id):
    # Allow any authenticated user to review files
    xml_file = XMLFile.query.get_or_404(file_id)
        
    xml_file = XMLFile.query.get_or_404(file_id)
    
    # Get records from all intermediate tables for this XML file
    mm320t_records = MM320T_SOUM_ACCORDE2106_Int.query.filter_by(xml_file_id=file_id).all()
    mm110t_records = MM110T_OPM_JOUR2106_Int.query.filter_by(xml_file_id=file_id).all()
    mm319t_records = MM319T_SOUM_BQ2106_Int.query.filter_by(xml_file_id=file_id).all()
    mm334t_records = MM334T_SOUM_BQ2106_Int.query.filter_by(xml_file_id=file_id).all()
    
    return render_template('review.html', 
                          xml_file=xml_file,
                          mm320t_records=mm320t_records,
                          mm110t_records=mm110t_records,
                          mm319t_records=mm319t_records,
                          mm334t_records=mm334t_records)

@app.route('/api/validate-record', methods=['POST'])
@login_required
def validate_record():
    # Allow any authenticated user to validate records
    try:
        data = request.json
        table_name = data.get('table')
        record_id = data.get('id')
        action = data.get('action')  # 'approve' or 'reject'
        
        if not all([table_name, record_id, action]):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
            
        # Map table names to model classes
        table_map = {
            'mm320t': MM320T_SOUM_ACCORDE2106_Int,
            'mm110t': MM110T_OPM_JOUR2106_Int,
            'mm319t': MM319T_SOUM_BQ2106_Int,
            'mm334t': MM334T_SOUM_BQ2106_Int
        }
        
        # Map to final tables
        final_table_map = {
            'mm320t': MM320T_SOUM_ACCORDE2106_Final,
            'mm110t': MM110T_OPM_JOUR2106_Final,
            'mm319t': MM319T_SOUM_BQ2106_Final,
            'mm334t': MM334T_SOUM_BQ2106_Final
        }
        
        # Get the appropriate model class
        model_class = table_map.get(table_name)
        final_model_class = final_table_map.get(table_name)
        
        if not model_class or not final_model_class:
            return jsonify({'status': 'error', 'message': 'Invalid table name'}), 400
            
        # Get the record
        record = model_class.query.get(record_id)
        
        if not record:
            return jsonify({'status': 'error', 'message': 'Record not found'}), 404
            
        if action == 'approve':
            # Create a new record in the final table
            final_record = final_model_class(
                DATE_OPER=record.DATE_OPER,
                CODE_OPER=record.CODE_OPER,
                DONNEUR=record.DONNEUR,
                RECEVEUR=record.RECEVEUR,
                NUM_OPER=record.NUM_OPER,
                MONT=record.MONT,
                TAUX=record.TAUX,
                DUREE=record.DUREE,
                DATE_ECH=record.DATE_ECH,
                TYPE_PLACE=record.TYPE_PLACE,
                DATE_REGL=record.DATE_REGL,
                FLAGCPT_ADMIS=record.FLAGCPT_ADMIS,
                FLAGCPT_TOMBE=record.FLAGCPT_TOMBE,
                NBRBON=record.NBRBON,
                ETAT_OPER=record.ETAT_OPER,
                NUM_OPER_GESTION=record.NUM_OPER_GESTION,
                UTILISATEUR=record.UTILISATEUR,
                DATE_SAISIE=datetime.now(),
                ACCEP_CP=record.ACCEP_CP,
                CODE_ISIN=record.CODE_ISIN,
                original_id=record.id
            )
            db.session.add(final_record)
            record.validation_status = 'approved'
        else:  # reject
            record.validation_status = 'rejected'
        
        db.session.commit()
        
        # Check if all records for this XML file have been processed
        xml_file = XMLFile.query.get(record.xml_file_id)
        
        all_records_processed = True
        for model in table_map.values():
            pending_records = model.query.filter_by(
                xml_file_id=xml_file.id, 
                validation_status='pending'
            ).count()
            if pending_records > 0:
                all_records_processed = False
                break
                
        if all_records_processed:
            xml_file.status = 'validated'
            db.session.commit()
        
        return jsonify({
            'status': 'success', 
            'message': f'Record {action}d successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error validating record: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/validate-all', methods=['POST'])
@login_required
def validate_all():
    # Allow any authenticated user to validate all records
        
    try:
        data = request.json
        file_id = data.get('file_id')
        action = data.get('action')  # 'approve' or 'reject'
        
        if not all([file_id, action]):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
            
        xml_file = XMLFile.query.get_or_404(file_id)
        
        # Tables to process
        tables = [
            (MM320T_SOUM_ACCORDE2106_Int, MM320T_SOUM_ACCORDE2106_Final),
            (MM110T_OPM_JOUR2106_Int, MM110T_OPM_JOUR2106_Final),
            (MM319T_SOUM_BQ2106_Int, MM319T_SOUM_BQ2106_Final),
            (MM334T_SOUM_BQ2106_Int, MM334T_SOUM_BQ2106_Final)
        ]
        
        # Process all records for this file
        for int_model, final_model in tables:
            records = int_model.query.filter_by(
                xml_file_id=file_id, 
                validation_status='pending'
            ).all()
            
            for record in records:
                if action == 'approve':
                    # Create a new record in the final table
                    final_record = final_model(
                        DATE_OPER=record.DATE_OPER,
                        CODE_OPER=record.CODE_OPER,
                        DONNEUR=record.DONNEUR,
                        RECEVEUR=record.RECEVEUR,
                        NUM_OPER=record.NUM_OPER,
                        MONT=record.MONT,
                        TAUX=record.TAUX,
                        DUREE=record.DUREE,
                        DATE_ECH=record.DATE_ECH,
                        TYPE_PLACE=record.TYPE_PLACE,
                        DATE_REGL=record.DATE_REGL,
                        FLAGCPT_ADMIS=record.FLAGCPT_ADMIS,
                        FLAGCPT_TOMBE=record.FLAGCPT_TOMBE,
                        NBRBON=record.NBRBON,
                        ETAT_OPER=record.ETAT_OPER,
                        NUM_OPER_GESTION=record.NUM_OPER_GESTION,
                        UTILISATEUR=record.UTILISATEUR,
                        DATE_SAISIE=datetime.now(),
                        ACCEP_CP=record.ACCEP_CP,
                        CODE_ISIN=record.CODE_ISIN,
                        original_id=record.id
                    )
                    db.session.add(final_record)
                    record.validation_status = 'approved'
                else:  # reject
                    record.validation_status = 'rejected'
        
        # Mark the XML file as validated
        xml_file.status = 'validated'
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'All records {action}d successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in batch validation: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
