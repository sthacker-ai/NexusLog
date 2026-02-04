"""
NexusLog Flask API
Main backend application
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

from models import get_session, Entry, Category, ContentIdea, Project, Config
from ai_services import AIServiceManager
from category_manager import CategoryManager
from sheets_integration import SheetsIntegration

# Load environment variables
load_dotenv()

# Initialize managers
import logging

# Configure Logging
# We use StreamHandler because start_app.bat redirects stdout/stderr to the log file.
# This prevents "PermissionError" (file locking) while keeping timestamps.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

ai_manager = AIServiceManager()
category_manager = CategoryManager()

try:
    sheets = SheetsIntegration()
except Exception as e:
    print(f"Google Sheets not configured: {e}")
    sheets = None


# ========================================
# Health Check
# ========================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'NexusLog API'})

@app.route('/api/system-status', methods=['GET'])
def system_status():
    """Detailed system status"""
    from health import get_system_status
    return jsonify(get_system_status())

@app.route('/api/logs/<service>', methods=['GET'])
def get_service_logs(service):
    """Get tail of logs for a service"""
    log_map = {
        'backend': 'logs/backend.log',
        'bot': 'logs/bot.log',
        'frontend': 'logs/frontend.log' # Note: frontend logs might be tricky if handled by shell redirection 
    }
    
    file_path = log_map.get(service)
    if not file_path or not os.path.exists(file_path):
        return jsonify({'error': 'Log file not found'}), 404
    
    try:
        # Read last 100 lines
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            return jsonify({'logs': lines[-100:]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========================================
# Entries Endpoints
# ========================================

@app.route('/api/entries', methods=['GET'])
def get_entries():
    """Get all entries with optional filtering"""
    session = get_session()
    try:
        category_id = request.args.get('category_id', type=int)
        content_type = request.args.get('content_type')
        limit = request.args.get('limit', 50, type=int)
        
        query = session.query(Entry)
        
        if category_id:
            query = query.filter(Entry.category_id == category_id)
        if content_type:
            query = query.filter(Entry.content_type == content_type)
        
        entries = query.order_by(Entry.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'entries': [entry.to_dict() for entry in entries],
            'count': len(entries)
        })
    finally:
        session.close()


@app.route('/api/entries/<int:entry_id>', methods=['GET'])
def get_entry(entry_id):
    """Get a specific entry"""
    session = get_session()
    try:
        entry = session.query(Entry).filter(Entry.id == entry_id).first()
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404
        
        return jsonify(entry.to_dict())
    finally:
        session.close()


@app.route('/api/entries', methods=['POST'])
def create_entry():
    """Create a new entry manually"""
    data = request.json
    session = get_session()
    
    try:
        content = data.get('content')
        content_type = data.get('content_type', 'text')
        use_ai = data.get('use_ai', False)
        is_content_idea = data.get('is_content_idea', False)
        output_types = data.get('output_types', [])
        category_id = data.get('category_id')
        subcategory_id = data.get('subcategory_id')
        
        if not content:
            return jsonify({'error': 'Content is required'}), 400
        
        # Validate and sanitize IDs
        if category_id == '': category_id = None
        if subcategory_id == '': subcategory_id = None
        
        # Use AI for categorization if requested
        if use_ai and not category_id:
            category_info = category_manager.suggest_category(content)
            category_id = category_info.get('category_id')
            subcategory_id = category_info.get('subcategory_id')
            is_content_idea = is_content_idea or category_info.get('is_content_idea', False)
        
        # Create entry
        entry = Entry(
            raw_content=content,
            processed_content=content,
            content_type=content_type,
            category_id=category_id,
            subcategory_id=subcategory_id,
            source='manual',
            entry_metadata={
                'is_content_idea': is_content_idea,
                'output_types': output_types
            }
        )
        session.add(entry)
        session.flush()
        
        # Create content idea if applicable
        if is_content_idea:
            ai_prompt = ai_manager.generate_content_prompt(content)
            
            content_idea = ContentIdea(
                entry_id=entry.id,
                idea_description=content,
                ai_prompt=ai_prompt,
                output_types=output_types,
                status='idea'
            )
            session.add(content_idea)
            
            # Sync to Google Sheets
            if sheets:
                try:
                    sheets.append_content_idea(content, ai_prompt, output_types)
                except Exception as e:
                    print(f"Error syncing to Google Sheets: {e}")
        
        session.commit()
        
        return jsonify({
            'message': 'Entry created successfully',
            'entry_id': entry.id
        }), 201
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        session.rollback()
        return jsonify({'error': str(e)}), 500
    
    finally:
        session.close()


@app.route('/api/entries/<int:entry_id>', methods=['DELETE'])
def delete_entry(entry_id):
    """Delete an entry"""
    session = get_session()
    try:
        entry = session.query(Entry).filter(Entry.id == entry_id).first()
        if not entry:
            return jsonify({'error': 'Entry not found'}), 404
        
        session.delete(entry)
        session.commit()
        
        return jsonify({'success': True})
    finally:
        session.close()


# ========================================
# Categories Endpoints
# ========================================

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all categories"""
    categories = category_manager.get_all_categories()
    return jsonify({'categories': categories})


@app.route('/api/categories', methods=['POST'])
def create_category():
    """Create a new category"""
    data = request.json
    
    try:
        name = data.get('name')
        description = data.get('description')
        parent_id = data.get('parent_id')
        
        if not name:
            return jsonify({'error': 'Name is required'}), 400
        
        category = category_manager.create_category(name, description, parent_id)
        return jsonify({'success': True, 'category': category}), 201
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@app.route('/api/categories/<int:category_id>', methods=['PUT'])
def update_category(category_id):
    """Update a category"""
    data = request.json
    
    try:
        category = category_manager.update_category(
            category_id,
            name=data.get('name'),
            description=data.get('description')
        )
        return jsonify({'success': True, 'category': category})
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """Delete a category"""
    success = category_manager.delete_category(category_id)
    
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Category not found'}), 404


@app.route('/api/categories/<int:parent_id>/subcategories', methods=['GET'])
def get_subcategories(parent_id):
    """Get subcategories for a parent category"""
    subcategories = category_manager.get_subcategories(parent_id)
    return jsonify({'subcategories': subcategories})


# ========================================
# Content Ideas Endpoints
# ========================================

@app.route('/api/content-ideas', methods=['GET'])
def get_content_ideas():
    """Get all content ideas"""
    session = get_session()
    try:
        output_type = request.args.get('output_type')
        limit = request.args.get('limit', 50, type=int)
        
        query = session.query(ContentIdea)
        
        # Filter by output type if specified
        if output_type:
            query = query.filter(ContentIdea.output_types.contains([output_type]))
        
        ideas = query.order_by(ContentIdea.created_at.desc()).limit(limit).all()
        
        return jsonify({
            'ideas': [idea.to_dict() for idea in ideas],
            'count': len(ideas)
        })
    finally:
        session.close()


@app.route('/api/content-ideas/<int:idea_id>', methods=['PUT'])
def update_content_idea(idea_id):
    """Update a content idea"""
    data = request.json
    session = get_session()
    
    try:
        idea = session.query(ContentIdea).filter(ContentIdea.id == idea_id).first()
        if not idea:
            return jsonify({'error': 'Content idea not found'}), 404
        
        if 'status' in data:
            idea.status = data['status']
        if 'output_types' in data:
            idea.output_types = data['output_types']
        
        session.commit()
        
        return jsonify({'success': True, 'idea': idea.to_dict()})
    finally:
        session.close()


# ========================================
# Projects Endpoints
# ========================================

@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    session = get_session()
    try:
        projects = session.query(Project).order_by(Project.created_at.desc()).all()
        return jsonify({
            'projects': [project.to_dict() for project in projects],
            'count': len(projects)
        })
    finally:
        session.close()


@app.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project"""
    data = request.json
    session = get_session()
    
    try:
        name = data.get('name')
        description = data.get('description')
        category_id = data.get('category_id')
        
        if not name:
            return jsonify({'error': 'Name is required'}), 400
        
        project = Project(
            name=name,
            description=description,
            category_id=category_id,
            tasks=[],
            status='idea'
        )
        session.add(project)
        session.commit()
        
        return jsonify({'success': True, 'project': project.to_dict()}), 201
    finally:
        session.close()


# ========================================
# Configuration Endpoints
# ========================================

@app.route('/api/config', methods=['GET'])
def get_config():
    """Get all configuration"""
    session = get_session()
    try:
        configs = session.query(Config).all()
        return jsonify({
            'config': {config.key: config.value for config in configs}
        })
    finally:
        session.close()


@app.route('/api/config/<key>', methods=['PUT'])
def update_config(key):
    """Update a configuration value"""
    data = request.json
    session = get_session()
    
    try:
        config = session.query(Config).filter(Config.key == key).first()
        
        if config:
            config.value = data.get('value')
        else:
            config = Config(key=key, value=data.get('value'))
            session.add(config)
        
        session.commit()
        
        return jsonify({'success': True, 'config': config.to_dict()})
    finally:
        session.close()


# ========================================
# Stats Endpoint
# ========================================

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get dashboard statistics"""
    session = get_session()
    try:
        total_entries = session.query(Entry).count()
        total_ideas = session.query(ContentIdea).count()
        total_projects = session.query(Project).count()
        total_categories = session.query(Category).filter(Category.parent_id == None).count()
        
        # Recent entries by type
        entries_by_type = {}
        for content_type in ['text', 'image', 'audio', 'video', 'link']:
            count = session.query(Entry).filter(Entry.content_type == content_type).count()
            entries_by_type[content_type] = count
        
        return jsonify({
            'total_entries': total_entries,
            'total_ideas': total_ideas,
            'total_projects': total_projects,
            'total_categories': total_categories,
            'entries_by_type': entries_by_type
        })
    finally:
        session.close()


# ========================================
# Telegram Webhook (for production)
# ========================================

@app.route('/api/telegram/webhook', methods=['POST'])
def telegram_webhook():
    """Handle Telegram webhook"""
    # This will be implemented when deploying to production
    # For now, we'll run the bot in polling mode
    return jsonify({'status': 'webhook received'})


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
