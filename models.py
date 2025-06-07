from datetime import datetime
from app import db


class User(db.Model):
    """Модель пользователя Битрикс24"""
    id = db.Column(db.Integer, primary_key=True)
    bitrix_user_id = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255))
    department = db.Column(db.String(255))
    position = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    conversations = db.relationship('Conversation', backref='user', lazy=True)


class Conversation(db.Model):
    """Модель разговора с ботом"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    chat_id = db.Column(db.String(100), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')  # active, closed, escalated
    escalated_to_human = db.Column(db.Boolean, default=False)
    
    messages = db.relationship('Message', backref='conversation', lazy=True, cascade='all, delete-orphan')


class Message(db.Model):
    """Модель сообщения в разговоре"""
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    message_type = db.Column(db.String(20), nullable=False)  # user, bot, system
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    processed_by_gpt = db.Column(db.Boolean, default=False)
    response_time = db.Column(db.Float)  # время ответа в секундах
    knowledge_base_used = db.Column(db.Boolean, default=False)


class KnowledgeBaseArticle(db.Model):
    """Модель статьи базы знаний"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    tags = db.Column(db.String(500))  # comma-separated tags
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    usage_count = db.Column(db.Integer, default=0)
    
    def get_tags_list(self):
        """Возвращает список тегов"""
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()] if self.tags else []


class BotResponse(db.Model):
    """Модель предопределенных ответов бота"""
    id = db.Column(db.Integer, primary_key=True)
    trigger_keywords = db.Column(db.String(500), nullable=False)  # ключевые слова для активации
    response_text = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    priority = db.Column(db.Integer, default=0)  # приоритет ответа
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    usage_count = db.Column(db.Integer, default=0)


class Analytics(db.Model):
    """Модель для аналитики работы бота"""
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    total_messages = db.Column(db.Integer, default=0)
    unique_users = db.Column(db.Integer, default=0)
    avg_response_time = db.Column(db.Float, default=0.0)
    escalated_conversations = db.Column(db.Integer, default=0)
    knowledge_base_hits = db.Column(db.Integer, default=0)
    most_common_category = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
