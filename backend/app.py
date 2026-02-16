"""
NexusLog Flask API
Main backend application
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import re

from models import get_session, Entry, Category, ContentIdea, Project, Config
from ai_services import AIServiceManager
from category_manager import CategoryManager
from sheets_integration import SheetsIntegration

# Load environment variables
load_dotenv()

# Initialize managers
import logging
import os

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Configure Logging - both console and file output
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.StreamHandler(),  # Console output
        logging.FileHandler('logs/backend.log', mode='a', encoding='utf-8')  # File output
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Security: Patterns to redact from logs before displaying
SENSITIVE_PATTERNS = [
    (r'[0-9]{8,10}:[A-Za-z0-9_-]{35,}', '[TELEGRAM_TOKEN_REDACTED]'),  # Telegram bot tokens
    (r'AIza[A-Za-z0-9_-]{35}', '[GOOGLE_API_KEY_REDACTED]'),  # Google API keys
    (r'sk-[A-Za-z0-9]{48,}', '[OPENAI_KEY_REDACTED]'),  # OpenAI API keys
    (r'r8_[A-Za-z0-9]{40,}', '[REPLICATE_KEY_REDACTED]'),  # Replicate API keys
    (r'gsk_[A-Za-z0-9]{50,}', '[GROQ_KEY_REDACTED]'),  # Groq API keys
    (r'postgresql://[^\s]+', '[DATABASE_URL_REDACTED]'),  # DB connection strings
    (r'password[=:][^\s]+', '[PASSWORD_REDACTED]'),  # Passwords in logs
]

def sanitize_log_line(line: str) -> str:
    """Remove sensitive information from a log line before display"""
    result = line
    for pattern, replacement in SENSITIVE_PATTERNS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result

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


@app.route('/api/usage', methods=['GET'])
def get_usage_stats():
    """Get AI usage statistics
    
    Query params:
        - days: Number of days to fetch (default: 7)
    
    Returns aggregated usage by model and day.
    """
    from models import get_session, UsageLog
    from datetime import datetime, timedelta
    from sqlalchemy import func
    from collections import defaultdict
    
    session = get_session()
    try:
        days = request.args.get('days', 7, type=int)
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all usage logs in the period
        logs = session.query(UsageLog).filter(
            UsageLog.timestamp >= cutoff_date
        ).order_by(UsageLog.timestamp.desc()).all()
        
        # Aggregate by date and model
        daily_usage = defaultdict(lambda: defaultdict(lambda: {
            'requests': 0,
            'input_tokens': 0,
            'output_tokens': 0,
            'cost_usd': 0.0
        }))
        
        model_totals = defaultdict(lambda: {
            'requests': 0,
            'input_tokens': 0,
            'output_tokens': 0,
            'cost_usd': 0.0
        })
        
        for log in logs:
            date_key = log.timestamp.strftime('%Y-%m-%d')
            model_key = f"{log.provider}/{log.model}" if log.model else log.provider
            
            daily_usage[date_key][model_key]['requests'] += 1
            daily_usage[date_key][model_key]['input_tokens'] += log.input_tokens or 0
            daily_usage[date_key][model_key]['output_tokens'] += log.output_tokens or 0
            daily_usage[date_key][model_key]['cost_usd'] += log.cost_usd or 0.0
            
            model_totals[model_key]['requests'] += 1
            model_totals[model_key]['input_tokens'] += log.input_tokens or 0
            model_totals[model_key]['output_tokens'] += log.output_tokens or 0
            model_totals[model_key]['cost_usd'] += log.cost_usd or 0.0
        
        # Convert to list format
        daily_list = []
        for date_key in sorted(daily_usage.keys(), reverse=True):
            day_entry = {
                'date': date_key,
                'models': []
            }
            for model_name, stats in daily_usage[date_key].items():
                day_entry['models'].append({
                    'model': model_name,
                    **stats
                })
            daily_list.append(day_entry)
        
        model_list = [
            {'model': name, **stats}
            for name, stats in sorted(model_totals.items(), key=lambda x: x[1]['requests'], reverse=True)
        ]
        
        # Overall totals
        total_requests = sum(m['requests'] for m in model_list)
        total_input = sum(m['input_tokens'] for m in model_list)
        total_output = sum(m['output_tokens'] for m in model_list)
        total_cost = sum(m['cost_usd'] for m in model_list)
        
        return jsonify({
            'daily': daily_list,
            'by_model': model_list,
            'totals': {
                'requests': total_requests,
                'input_tokens': total_input,
                'output_tokens': total_output,
                'cost_usd': round(total_cost, 6)
            },
            'days': days
        })
    finally:
        session.close()

@app.route('/api/logs/<service>', methods=['GET'])
def get_service_logs(service):
    """Get logs for a service with pagination support
    
    Query params:
        - offset: Starting position from the end of file (0 = latest, default: 0)
        - limit: Number of lines to return (default: 50)
    
    Returns logs in descending order (latest first) with total line count.
    """
    log_map = {
        'backend': 'logs/backend.log',
        'bot': 'logs/bot.log',
        'frontend': 'logs/frontend.log'
    }
    
    file_path = log_map.get(service)
    if not file_path or not os.path.exists(file_path):
        return jsonify({'error': 'Log file not found', 'logs': [], 'total': 0}), 404
    
    try:
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
        
        total = len(lines)
        
        # Reverse to get latest first
        lines = lines[::-1]
        
        # Apply offset and limit
        paginated = lines[offset:offset + limit]
        
        # Check if there are more lines to load
        has_more = (offset + limit) < total
        
        # Sanitize logs before returning to frontend
        sanitized_logs = [sanitize_log_line(line) for line in paginated]
        
        return jsonify({
            'logs': sanitized_logs,
            'total': total,
            'offset': offset,
            'limit': limit,
            'has_more': has_more
        })
    except Exception as e:
        return jsonify({'error': str(e), 'logs': [], 'total': 0}), 500


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


@app.route('/api/entries/by-date', methods=['GET'])
def get_entries_by_date():
    """Get entries grouped by date for timeline view
    
    Query params:
        - days: Number of days to fetch (default: 30)
    
    Returns entries grouped by date, latest first.
    """
    session = get_session()
    try:
        from datetime import datetime, timedelta
        from collections import defaultdict
        
        days = request.args.get('days', 30, type=int)
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        entries = session.query(Entry)\
            .filter(Entry.created_at >= cutoff_date)\
            .order_by(Entry.created_at.desc())\
            .all()
        
        # Group by date
        grouped = defaultdict(list)
        for entry in entries:
            date_key = entry.created_at.strftime('%Y-%m-%d')
            grouped[date_key].append(entry.to_dict())
        
        # Convert to sorted list of date groups
        timeline = []
        for date_key in sorted(grouped.keys(), reverse=True):
            timeline.append({
                'date': date_key,
                'entries': grouped[date_key]
            })
        
        return jsonify({
            'timeline': timeline,
            'total_entries': len(entries),
            'days_covered': days
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


@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    """Get usage analytics data
    
    Returns:
        - last_7_days: Daily entry counts for the past 7 days
        - text_vs_voice: Ratio of text entries vs audio entries
        - top_categories: Most used categories
        - weekly_total: Total entries this week
        - daily_average: Average entries per day
    """
    session = get_session()
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func
        from collections import defaultdict
        
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=6)
        
        # Get entries from last 7 days
        recent_entries = session.query(Entry).filter(
            func.date(Entry.created_at) >= week_ago
        ).all()
        
        # Group by date for the chart
        daily_counts = defaultdict(int)
        for entry in recent_entries:
            date_key = entry.created_at.strftime('%Y-%m-%d')
            daily_counts[date_key] += 1
        
        # Build last 7 days data (fill in zeros for missing days)
        last_7_days = []
        for i in range(6, -1, -1):
            date = today - timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            day_name = date.strftime('%a')  # Mon, Tue, etc.
            last_7_days.append({
                'date': date_str,
                'day': day_name,
                'count': daily_counts.get(date_str, 0)
            })
        
        # Text vs Voice ratio
        text_count = session.query(Entry).filter(Entry.content_type == 'text').count()
        audio_count = session.query(Entry).filter(Entry.content_type == 'audio').count()
        
        # Top categories (last 30 days)
        month_ago = today - timedelta(days=30)
        category_counts = session.query(
            Category.name, func.count(Entry.id)
        ).join(Entry, Entry.category_id == Category.id)\
         .filter(func.date(Entry.created_at) >= month_ago)\
         .group_by(Category.name)\
         .order_by(func.count(Entry.id).desc())\
         .limit(5)\
         .all()
        
        top_categories = [{'name': name, 'count': count} for name, count in category_counts]
        
        # Weekly stats
        weekly_total = len(recent_entries)
        daily_average = round(weekly_total / 7, 1)
        
        return jsonify({
            'last_7_days': last_7_days,
            'text_vs_voice': {
                'text': text_count,
                'audio': audio_count
            },
            'top_categories': top_categories,
            'weekly_total': weekly_total,
            'daily_average': daily_average
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


@app.route('/api/uploads/<path:filename>')
def serve_uploads(filename):
    """Serve uploaded files"""
    from flask import send_from_directory
    return send_from_directory('static/uploads', filename)


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
