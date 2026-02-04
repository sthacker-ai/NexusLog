"""
NexusLog Database Models
SQLAlchemy ORM models for PostgreSQL
"""
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey('categories.id', ondelete='CASCADE'))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    parent = relationship('Category', remote_side=[id], backref='subcategories')
    entries = relationship('Entry', foreign_keys='Entry.category_id', back_populates='category')
    projects = relationship('Project', back_populates='category')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'parent_id': self.parent_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'subcategories': [sub.to_dict() for sub in self.subcategories] if self.subcategories else []
        }


class Entry(Base):
    __tablename__ = 'entries'
    
    id = Column(Integer, primary_key=True)
    raw_content = Column(Text)
    processed_content = Column(Text)
    content_type = Column(String(50), nullable=False)  # text, image, video, audio, link
    file_path = Column(String(500))
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='SET NULL'))
    subcategory_id = Column(Integer, ForeignKey('categories.id', ondelete='SET NULL'))
    source = Column(String(50), default='telegram')
    entry_metadata = Column('metadata', JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = relationship('Category', foreign_keys=[category_id], back_populates='entries')
    subcategory = relationship('Category', foreign_keys=[subcategory_id])
    content_ideas = relationship('ContentIdea', back_populates='entry', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'raw_content': self.raw_content,
            'processed_content': self.processed_content,
            'content_type': self.content_type,
            'file_path': self.file_path,
            'category': self.category.to_dict() if self.category else None,
            'subcategory': self.subcategory.to_dict() if self.subcategory else None,
            'source': self.source,
            'entry_metadata': self.entry_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'content_ideas': [idea.to_dict() for idea in self.content_ideas] if self.content_ideas else []
        }


class ContentIdea(Base):
    __tablename__ = 'content_ideas'
    
    id = Column(Integer, primary_key=True)
    entry_id = Column(Integer, ForeignKey('entries.id', ondelete='CASCADE'))
    title = Column(String(200))  # Short AI-generated title
    idea_description = Column(Text, nullable=False)  # Full processed content
    ai_prompt = Column(Text)  # Keep for historical data, but not displayed
    output_types = Column(JSON, default=[])  # ["blog", "youtube", "linkedin", "shorts", "reels"]
    status = Column(String(50), default='idea')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    entry = relationship('Entry', back_populates='content_ideas')
    
    def to_dict(self):
        return {
            'id': self.id,
            'entry_id': self.entry_id,
            'title': self.title,
            'idea_description': self.idea_description,
            'ai_prompt': self.ai_prompt,
            'output_types': self.output_types,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Project(Base):
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey('categories.id', ondelete='SET NULL'))
    tasks = Column(JSON, default=[])
    status = Column(String(50), default='idea')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = relationship('Category', back_populates='projects')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category.to_dict() if self.category else None,
            'tasks': self.tasks,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Config(Base):
    __tablename__ = 'config'
    
    key = Column(String(100), primary_key=True)
    value = Column(JSON, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'key': self.key,
            'value': self.value,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class UsageLog(Base):
    __tablename__ = 'usage_logs'
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    provider = Column(String(50))
    model = Column(String(100))
    feature = Column(String(50))
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost_usd = Column(Integer, default=0) # Actually create as Numeric/Float in SQL, mapped as Float here
    # Correction: In SQL it's DECIMAL(10,6). SQLAlchemy Generic matching:
    from sqlalchemy import Float
    cost_usd = Column(Float, default=0.0)
    details = Column(JSON, default={})
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'provider': self.provider,
            'model': self.model,
            'feature': self.feature,
            'cost_usd': self.cost_usd,
            'details': self.details
        }


# Database connection
def get_engine():
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        raise ValueError("DATABASE_URL not set in environment variables")
    return create_engine(database_url)


def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()


def init_db():
    """Initialize database tables"""
    engine = get_engine()
    Base.metadata.create_all(engine)
