from flask import Blueprint, jsonify, request, abort
from src.models.note import Note, db
import json
from datetime import datetime

note_bp = Blueprint('note', __name__)

@note_bp.route('/notes', methods=['GET'])
def get_notes():
    """Get all notes, ordered by most recently updated"""
    notes = Note.query.order_by(Note.updated_at.desc()).all()
    return jsonify([note.to_dict() for note in notes])

@note_bp.route('/notes', methods=['POST'])
def create_note():
    """Create a new note"""
    try:
        data = request.json
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({'error': 'Title and content are required'}), 400

        # handle tags: allow JSON array or comma-separated string
        tags_field = data.get('tags')
        tags_text = None
        if isinstance(tags_field, list):
            tags_text = json.dumps(tags_field)
        elif isinstance(tags_field, str):
            # try parse JSON string first
            try:
                parsed = json.loads(tags_field)
                if isinstance(parsed, list):
                    tags_text = json.dumps(parsed)
                else:
                    # fallback to comma-separated
                    tags_text = json.dumps([t.strip() for t in tags_field.split(',') if t.strip()])
            except Exception:
                tags_text = json.dumps([t.strip() for t in tags_field.split(',') if t.strip()])

        # handle event dates (ISO strings)
        esd = data.get('event_start_date')
        eed = data.get('event_end_date')
        start_dt = None
        end_dt = None
        try:
            if esd:
                start_dt = datetime.fromisoformat(esd)
            if eed:
                end_dt = datetime.fromisoformat(eed)
        except Exception as ex:
            return jsonify({'error': f'Invalid datetime format: {ex}'}), 400

        if start_dt and end_dt and end_dt < start_dt:
            return jsonify({'error': 'event_end_date must be >= event_start_date'}), 400

        note = Note(title=data['title'], content=data['content'], tags=tags_text,
                    event_start_date=start_dt, event_end_date=end_dt)
        db.session.add(note)
        db.session.commit()
        return jsonify(note.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    """Get a specific note by ID"""
    note = Note.query.get_or_404(note_id)
    return jsonify(note.to_dict())

@note_bp.route('/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    """Update a specific note"""
    try:
        note = Note.query.get_or_404(note_id)
        data = request.json

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        note.title = data.get('title', note.title)
        note.content = data.get('content', note.content)

        # tags
        if 'tags' in data:
            tags_field = data.get('tags')
            if isinstance(tags_field, list):
                note.tags = json.dumps(tags_field)
            elif isinstance(tags_field, str):
                try:
                    parsed = json.loads(tags_field)
                    if isinstance(parsed, list):
                        note.tags = json.dumps(parsed)
                    else:
                        note.tags = json.dumps([t.strip() for t in tags_field.split(',') if t.strip()])
                except Exception:
                    note.tags = json.dumps([t.strip() for t in tags_field.split(',') if t.strip()])

        # event dates
        esd = data.get('event_start_date')
        eed = data.get('event_end_date')
        try:
            if esd is not None:
                note.event_start_date = datetime.fromisoformat(esd) if esd else None
            if eed is not None:
                note.event_end_date = datetime.fromisoformat(eed) if eed else None
        except Exception as ex:
            return jsonify({'error': f'Invalid datetime format: {ex}'}), 400

        if note.event_start_date and note.event_end_date and note.event_end_date < note.event_start_date:
            return jsonify({'error': 'event_end_date must be >= event_start_date'}), 400

        db.session.commit()
        return jsonify(note.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete a specific note"""
    try:
        note = Note.query.get_or_404(note_id)
        db.session.delete(note)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/search', methods=['GET'])
def search_notes():
    """Search notes by title or content"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    notes = Note.query.filter(
        (Note.title.contains(query)) | (Note.content.contains(query))
    ).order_by(Note.updated_at.desc()).all()
    
    return jsonify([note.to_dict() for note in notes])

