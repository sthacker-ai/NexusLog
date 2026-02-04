"""
NexusLog Category Manager
Smart category management with max 10 top-level categories
"""
from models import Category, get_session
from ai_services import AIServiceManager
from typing import Dict, Optional, List


class CategoryManager:
    """Manages categories with AI-powered suggestions"""
    
    def __init__(self):
        self.ai_manager = AIServiceManager()
        self.max_categories = 10
    
    def get_all_categories(self) -> List[Dict]:
        """Get all categories with subcategories"""
        session = get_session()
        try:
            # Get only top-level categories
            categories = session.query(Category).filter(Category.parent_id == None).all()
            return [cat.to_dict() for cat in categories]
        finally:
            session.close()
    
    def get_category_count(self) -> int:
        """Get count of top-level categories"""
        session = get_session()
        try:
            return session.query(Category).filter(Category.parent_id == None).count()
        finally:
            session.close()
    
    def get_category_by_name(self, name: str) -> Dict:
        """Get category info by name, returns dict with category_id"""
        session = get_session()
        try:
            # Try exact match first
            category = session.query(Category).filter(Category.name == name).first()
            
            # Try case-insensitive match if not found
            if not category:
                category = session.query(Category).filter(
                    Category.name.ilike(name)
                ).first()
            
            # Fall back to General Notes if not found
            if not category:
                category = session.query(Category).filter(
                    Category.name == 'General Notes'
                ).first()
            
            if category:
                return {
                    'category_id': category.id,
                    'category_name': category.name,
                    'subcategory_id': None,
                    'is_content_idea': False
                }
            return {
                'category_id': None,
                'category_name': None,
                'subcategory_id': None,
                'is_content_idea': False
            }
        finally:
            session.close()
    
    def create_category(self, name: str, description: str = None, parent_id: int = None) -> Dict:
        """Create a new category"""
        session = get_session()
        try:
            # Check if it's a top-level category
            if parent_id is None:
                count = self.get_category_count()
                if count >= self.max_categories:
                    raise ValueError(f"Maximum {self.max_categories} top-level categories reached")
            
            # Check if category already exists
            existing = session.query(Category).filter(Category.name == name).first()
            if existing:
                return existing.to_dict()
            
            category = Category(
                name=name,
                description=description,
                parent_id=parent_id
            )
            session.add(category)
            session.commit()
            result = category.to_dict()
            return result
        finally:
            session.close()
    
    def suggest_category(self, content: str) -> Dict:
        """
        Use AI to suggest appropriate category for content
        Returns: {
            'category_name': str,
            'category_id': int or None,
            'subcategory_name': str or None,
            'subcategory_id': int or None,
            'is_new': bool,
            'is_content_idea': bool
        }
        """
        # Get existing categories
        existing_categories = self.get_all_categories()
        
        # Use AI to categorize
        ai_result = self.ai_manager.categorize_content(content, existing_categories)
        
        session = get_session()
        try:
            category_name = ai_result.get('category', 'General Notes')
            is_new_category = ai_result.get('is_new_category', False)
            subcategory_name = ai_result.get('subcategory')
            is_content_idea = ai_result.get('is_content_idea', False)
            
            # Find or create category
            category = session.query(Category).filter(Category.name == category_name).first()
            
            if not category and is_new_category:
                # Check if we can create a new category
                if self.get_category_count() < self.max_categories:
                    category = Category(name=category_name, description=f"Auto-created category")
                    session.add(category)
                    session.commit()
                else:
                    # Default to General Notes if max reached
                    category = session.query(Category).filter(Category.name == 'General Notes').first()
            elif not category:
                # Default to General Notes
                category = session.query(Category).filter(Category.name == 'General Notes').first()
            
            # Handle subcategory
            subcategory = None
            if subcategory_name and category:
                subcategory = session.query(Category).filter(
                    Category.name == subcategory_name,
                    Category.parent_id == category.id
                ).first()
                
                if not subcategory:
                    # Create subcategory
                    subcategory = Category(
                        name=subcategory_name,
                        parent_id=category.id,
                        description="Auto-created subcategory"
                    )
                    session.add(subcategory)
                    session.commit()
            
            return {
                'category_name': category.name if category else None,
                'category_id': category.id if category else None,
                'subcategory_name': subcategory.name if subcategory else None,
                'subcategory_id': subcategory.id if subcategory else None,
                'is_new': is_new_category,
                'is_content_idea': is_content_idea
            }
        finally:
            session.close()
    
    def update_category(self, category_id: int, name: str = None, description: str = None) -> Dict:
        """Update category details"""
        session = get_session()
        try:
            category = session.query(Category).filter(Category.id == category_id).first()
            if not category:
                raise ValueError("Category not found")
            
            if name:
                category.name = name
            if description:
                category.description = description
            
            session.commit()
            return category.to_dict()
        finally:
            session.close()
    
    def delete_category(self, category_id: int) -> bool:
        """Delete a category"""
        session = get_session()
        try:
            category = session.query(Category).filter(Category.id == category_id).first()
            if not category:
                return False
            
            session.delete(category)
            session.commit()
            return True
        finally:
            session.close()
    
    def get_subcategories(self, parent_id: int) -> List[Dict]:
        """Get all subcategories for a parent category"""
        session = get_session()
        try:
            subcategories = session.query(Category).filter(Category.parent_id == parent_id).all()
            return [cat.to_dict() for cat in subcategories]
        finally:
            session.close()
