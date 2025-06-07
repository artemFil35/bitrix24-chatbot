import os
import json
import logging
from datetime import datetime, date, timedelta
from flask import render_template, request, jsonify, redirect, url_for, flash
from app import app, db
from models import User, Conversation, Message, KnowledgeBaseArticle, BotResponse, Analytics
from bitrix_client import BitrixClient
from yandex_gpt_client import YandexGPTClient
from knowledge_base import KnowledgeBaseManager
from sqlalchemy import func, desc

# Инициализация клиентов
bitrix_client = BitrixClient()
gpt_client = YandexGPTClient()
kb_manager = KnowledgeBaseManager()


@app.route('/')
def index():
    """Главная страница с обзором статистики"""
    # Получаем статистику за последние 7 дней
    week_ago = date.today() - timedelta(days=7)
    
    total_conversations = Conversation.query.count()
    active_conversations = Conversation.query.filter_by(status='active').count()
    total_users = User.query.filter_by(is_active=True).count()
    
    # Статистика сообщений за неделю
    week_messages = Message.query.join(Conversation).filter(
        Message.timestamp >= week_ago
    ).count()
    
    # Среднее время ответа
    avg_response = db.session.query(func.avg(Message.response_time)).filter(
        Message.response_time.isnot(None),
        Message.timestamp >= week_ago
    ).scalar() or 0
    
    # Популярные категории
    popular_categories = db.session.query(
        KnowledgeBaseArticle.category,
        func.sum(KnowledgeBaseArticle.usage_count).label('total_usage')
    ).group_by(KnowledgeBaseArticle.category).order_by(desc('total_usage')).limit(5).all()
    
    return render_template('index.html', 
                         total_conversations=total_conversations,
                         active_conversations=active_conversations,
                         total_users=total_users,
                         week_messages=week_messages,
                         avg_response_time=round(avg_response, 2),
                         popular_categories=popular_categories)


@app.route('/webhook/bitrix', methods=['POST'])
def bitrix_webhook():
    """Веб-хук для получения сообщений из Битрикс24"""
    try:
        data = request.get_json()
        if not data:
            logging.error("No data received in webhook")
            return jsonify({'error': 'No data received'}), 400
        
        # Логируем полученные данные
        logging.info(f"Received webhook data: {data}")
        
        # Извлекаем информацию о сообщении
        message_text = data.get('message', {}).get('text', '')
        user_id = data.get('user', {}).get('id')
        chat_id = data.get('chat', {}).get('id')
        user_name = data.get('user', {}).get('name', 'Неизвестный пользователь')
        
        if not all([message_text, user_id, chat_id]):
            logging.error("Missing required fields in webhook data")
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Найти или создать пользователя
        user = User.query.filter_by(bitrix_user_id=str(user_id)).first()
        if not user:
            user = User(
                bitrix_user_id=str(user_id),
                name=user_name,
                email=data.get('user', {}).get('email', ''),
                department=data.get('user', {}).get('department', ''),
                position=data.get('user', {}).get('position', '')
            )
            db.session.add(user)
            db.session.commit()
        
        # Найти или создать разговор
        conversation = Conversation.query.filter_by(
            user_id=user.id,
            chat_id=str(chat_id),
            status='active'
        ).first()
        
        if not conversation:
            conversation = Conversation(
                user_id=user.id,
                chat_id=str(chat_id)
            )
            db.session.add(conversation)
            db.session.commit()
        
        # Сохранить сообщение пользователя
        user_message = Message(
            conversation_id=conversation.id,
            message_type='user',
            content=message_text
        )
        db.session.add(user_message)
        db.session.commit()
        
        # Обработать сообщение и получить ответ
        start_time = datetime.utcnow()
        bot_response = process_user_message(message_text, conversation)
        response_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Сохранить ответ бота
        bot_message = Message(
            conversation_id=conversation.id,
            message_type='bot',
            content=bot_response,
            processed_by_gpt=True,
            response_time=response_time
        )
        db.session.add(bot_message)
        db.session.commit()
        
        # Отправить ответ в Битрикс24
        bitrix_client.send_message(chat_id, bot_response)
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        logging.error(f"Error processing webhook: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


def process_user_message(message_text, conversation):
    """Обработка сообщения пользователя и генерация ответа"""
    try:
        # Сначала проверяем базу знаний
        kb_response = kb_manager.search_knowledge_base(message_text)
        if kb_response:
            return kb_response
        
        # Проверяем предопределенные ответы
        bot_response = get_predefined_response(message_text)
        if bot_response:
            return bot_response
        
        # Если ничего не найдено, обращаемся к YandexGPT
        context = get_conversation_context(conversation)
        gpt_response = gpt_client.generate_response(message_text, context)
        
        return gpt_response
        
    except Exception as e:
        logging.error(f"Error processing message: {str(e)}")
        return "Извините, произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже или обратитесь к HR-специалисту."


def get_predefined_response(message_text):
    """Поиск предопределенного ответа по ключевым словам"""
    message_lower = message_text.lower()
    
    responses = BotResponse.query.filter_by(is_active=True).order_by(desc(BotResponse.priority)).all()
    
    for response in responses:
        keywords = [kw.strip().lower() for kw in response.trigger_keywords.split(',')]
        if any(keyword in message_lower for keyword in keywords):
            response.usage_count += 1
            db.session.commit()
            return response.response_text
    
    return None


def get_conversation_context(conversation):
    """Получение контекста разговора для YandexGPT"""
    recent_messages = Message.query.filter_by(
        conversation_id=conversation.id
    ).order_by(desc(Message.timestamp)).limit(10).all()
    
    context = []
    for msg in reversed(recent_messages):
        role = "user" if msg.message_type == "user" else "assistant"
        context.append({"role": role, "content": msg.content})
    
    return context


@app.route('/admin')
def admin():
    """Админ-панель"""
    # Статистика для админ-панели
    total_articles = KnowledgeBaseArticle.query.filter_by(is_active=True).count()
    total_responses = BotResponse.query.filter_by(is_active=True).count()
    active_conversations = Conversation.query.filter_by(status='active').count()
    
    recent_conversations = Conversation.query.order_by(desc(Conversation.started_at)).limit(10).all()
    
    return render_template('admin.html',
                         total_articles=total_articles,
                         total_responses=total_responses,
                         active_conversations=active_conversations,
                         recent_conversations=recent_conversations)


@app.route('/analytics')
def analytics():
    """Страница аналитики"""
    # Данные для графиков за последние 30 дней
    thirty_days_ago = date.today() - timedelta(days=30)
    
    # Сообщения по дням
    daily_messages = db.session.query(
        func.date(Message.timestamp).label('date'),
        func.count(Message.id).label('count')
    ).filter(
        Message.timestamp >= thirty_days_ago
    ).group_by(func.date(Message.timestamp)).order_by('date').all()
    
    # Время ответа по дням
    daily_response_time = db.session.query(
        func.date(Message.timestamp).label('date'),
        func.avg(Message.response_time).label('avg_time')
    ).filter(
        Message.timestamp >= thirty_days_ago,
        Message.response_time.isnot(None)
    ).group_by(func.date(Message.timestamp)).order_by('date').all()
    
    # Популярные категории
    category_stats = db.session.query(
        KnowledgeBaseArticle.category,
        func.sum(KnowledgeBaseArticle.usage_count).label('usage')
    ).group_by(KnowledgeBaseArticle.category).order_by(desc('usage')).limit(10).all()
    
    return render_template('analytics.html',
                         daily_messages=daily_messages,
                         daily_response_time=daily_response_time,
                         category_stats=category_stats)


@app.route('/knowledge-base')
def knowledge_base():
    """Управление базой знаний"""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    query = KnowledgeBaseArticle.query
    
    if category:
        query = query.filter_by(category=category)
    
    if search:
        query = query.filter(KnowledgeBaseArticle.title.contains(search))
    
    articles = query.order_by(desc(KnowledgeBaseArticle.updated_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Получаем все категории для фильтра
    categories = db.session.query(KnowledgeBaseArticle.category).distinct().all()
    categories = [cat[0] for cat in categories]
    
    return render_template('knowledge_base.html',
                         articles=articles,
                         categories=categories,
                         current_category=category,
                         search_query=search)


@app.route('/api/knowledge-base', methods=['POST'])
def create_article():
    """Создание новой статьи в базе знаний"""
    try:
        data = request.get_json()
        
        article = KnowledgeBaseArticle(
            title=data['title'],
            content=data['content'],
            category=data['category'],
            tags=data.get('tags', '')
        )
        
        db.session.add(article)
        db.session.commit()
        
        return jsonify({'status': 'success', 'id': article.id}), 201
        
    except Exception as e:
        logging.error(f"Error creating article: {str(e)}")
        return jsonify({'error': 'Failed to create article'}), 500


@app.route('/api/knowledge-base/<int:article_id>', methods=['PUT'])
def update_article(article_id):
    """Обновление статьи в базе знаний"""
    try:
        article = KnowledgeBaseArticle.query.get_or_404(article_id)
        data = request.get_json()
        
        article.title = data['title']
        article.content = data['content']
        article.category = data['category']
        article.tags = data.get('tags', '')
        article.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        logging.error(f"Error updating article: {str(e)}")
        return jsonify({'error': 'Failed to update article'}), 500


@app.route('/api/knowledge-base/<int:article_id>', methods=['DELETE'])
def delete_article(article_id):
    """Удаление статьи из базы знаний"""
    try:
        article = KnowledgeBaseArticle.query.get_or_404(article_id)
        article.is_active = False
        db.session.commit()
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        logging.error(f"Error deleting article: {str(e)}")
        return jsonify({'error': 'Failed to delete article'}), 500


@app.route('/api/bot-responses', methods=['POST'])
def create_bot_response():
    """Создание нового предопределенного ответа"""
    try:
        data = request.get_json()
        
        response = BotResponse(
            trigger_keywords=data['keywords'],
            response_text=data['response'],
            category=data['category'],
            priority=data.get('priority', 0)
        )
        
        db.session.add(response)
        db.session.commit()
        
        return jsonify({'status': 'success', 'id': response.id}), 201
        
    except Exception as e:
        logging.error(f"Error creating bot response: {str(e)}")
        return jsonify({'error': 'Failed to create response'}), 500


@app.errorhandler(404)
def not_found_error(error):
    return render_template('base.html'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('base.html'), 500
