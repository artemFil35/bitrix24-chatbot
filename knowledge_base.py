import logging
from typing import Optional, List, Dict
from app import db
from models import KnowledgeBaseArticle


class KnowledgeBaseManager:
    """Менеджер для работы с базой знаний"""
    
    def __init__(self):
        self.categories = {
            'отпуск': ['отпуск', 'отгул', 'выходной', 'отдых', 'vacation'],
            'больничный': ['больничный', 'болезнь', 'медицина', 'здоровье', 'лечение'],
            'зарплата': ['зарплата', 'оплата', 'деньги', 'премия', 'бонус'],
            'документы': ['документ', 'справка', 'заявление', 'бумаги'],
            'рабочее время': ['время', 'график', 'смена', 'опоздание', 'переработка'],
            'льготы': ['льгота', 'компенсация', 'дополнительные выплаты', 'соцпакет'],
            'обучение': ['обучение', 'курсы', 'тренинг', 'развитие', 'навыки'],
            'оборудование': ['компьютер', 'техника', 'оборудование', 'ноутбук', 'телефон'],
            'офис': ['офис', 'рабочее место', 'парковка', 'столовая', 'кухня'],
            'коллеги': ['коллеги', 'команда', 'сотрудники', 'руководитель', 'начальник']
        }
    
    def search_knowledge_base(self, query: str) -> Optional[str]:
        """Поиск в базе знаний по запросу"""
        try:
            query_lower = query.lower()
            
            # Сначала ищем точные совпадения в заголовках
            exact_match = KnowledgeBaseArticle.query.filter(
                KnowledgeBaseArticle.is_active == True,
                KnowledgeBaseArticle.title.ilike(f'%{query}%')
            ).first()
            
            if exact_match:
                exact_match.usage_count += 1
                db.session.commit()
                return self._format_article_response(exact_match)
            
            # Ищем по ключевым словам в категориях
            relevant_category = self._find_relevant_category(query_lower)
            if relevant_category:
                articles = KnowledgeBaseArticle.query.filter(
                    KnowledgeBaseArticle.is_active == True,
                    KnowledgeBaseArticle.category == relevant_category
                ).order_by(KnowledgeBaseArticle.usage_count.desc()).limit(3).all()
                
                if articles:
                    # Возвращаем самую популярную статью из категории
                    best_article = articles[0]
                    best_article.usage_count += 1
                    db.session.commit()
                    return self._format_article_response(best_article)
            
            # Ищем по содержимому статей
            content_match = KnowledgeBaseArticle.query.filter(
                KnowledgeBaseArticle.is_active == True,
                KnowledgeBaseArticle.content.ilike(f'%{query}%')
            ).order_by(KnowledgeBaseArticle.usage_count.desc()).first()
            
            if content_match:
                content_match.usage_count += 1
                db.session.commit()
                return self._format_article_response(content_match)
            
            # Ищем по тегам
            tag_match = KnowledgeBaseArticle.query.filter(
                KnowledgeBaseArticle.is_active == True,
                KnowledgeBaseArticle.tags.ilike(f'%{query}%')
            ).order_by(KnowledgeBaseArticle.usage_count.desc()).first()
            
            if tag_match:
                tag_match.usage_count += 1
                db.session.commit()
                return self._format_article_response(tag_match)
            
            return None
            
        except Exception as e:
            logging.error(f"Error searching knowledge base: {str(e)}")
            return None
    
    def _find_relevant_category(self, query: str) -> Optional[str]:
        """Поиск релевантной категории по ключевым словам"""
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword in query:
                    return category
        return None
    
    def _format_article_response(self, article: KnowledgeBaseArticle) -> str:
        """Форматирование ответа из статьи базы знаний"""
        response = f"📋 **{article.title}**\n\n"
        response += article.content
        
        if article.get_tags_list():
            response += f"\n\n🏷️ Теги: {', '.join(article.get_tags_list())}"
        
        response += "\n\n💡 Если у вас остались вопросы, обратитесь к HR-специалисту."
        
        return response
    
    def get_popular_articles(self, limit: int = 5) -> List[KnowledgeBaseArticle]:
        """Получение популярных статей"""
        try:
            return KnowledgeBaseArticle.query.filter_by(
                is_active=True
            ).order_by(
                KnowledgeBaseArticle.usage_count.desc()
            ).limit(limit).all()
            
        except Exception as e:
            logging.error(f"Error getting popular articles: {str(e)}")
            return []
    
    def get_articles_by_category(self, category: str) -> List[KnowledgeBaseArticle]:
        """Получение статей по категории"""
        try:
            return KnowledgeBaseArticle.query.filter(
                KnowledgeBaseArticle.is_active == True,
                KnowledgeBaseArticle.category == category
            ).order_by(
                KnowledgeBaseArticle.usage_count.desc()
            ).all()
            
        except Exception as e:
            logging.error(f"Error getting articles by category: {str(e)}")
            return []
    
    def create_default_articles(self):
        """Создание статей по умолчанию"""
        try:
            default_articles = [
                {
                    'title': 'Как оформить отпуск',
                    'content': '''Для оформления отпуска необходимо:

1. Подать заявление на отпуск не менее чем за 2 недели до планируемой даты
2. Согласовать даты с непосредственным руководителем
3. Передать текущие дела коллегам или временно замещающему сотруднику
4. Уведомить клиентов о временном отсутствии (если применимо)

📝 Заявление подается через корпоративную систему или в кадровую службу.
⏰ Минимальная продолжительность отпуска - 3 дня.
📅 Ежегодный оплачиваемый отпуск составляет 28 календарных дней.''',
                    'category': 'отпуск',
                    'tags': 'отпуск, заявление, отдых, календарь'
                },
                {
                    'title': 'Процедура оформления больничного листа',
                    'content': '''При болезни необходимо:

1. В первый день болезни уведомить непосредственного руководителя до 10:00
2. Обратиться к врачу и получить больничный лист
3. В течение 3 дней после выздоровления предоставить больничный лист в кадровую службу
4. Заполнить уведомление о временной нетрудоспособности

💊 Больничный оплачивается согласно трудовому законодательству.
📋 Электронные больничные листы принимаются наравне с бумажными.
⚕️ При болезни более 3 дней обязательно предоставление медицинской справки.''',
                    'category': 'больничный',
                    'tags': 'больничный, болезнь, медицина, справка'
                },
                {
                    'title': 'График рабочего времени',
                    'content': '''Стандартный рабочий график:

🕘 Начало рабочего дня: 9:00
🕔 Окончание рабочего дня: 18:00
🕐 Обеденный перерыв: 13:00-14:00
📅 Рабочие дни: понедельник-пятница

Гибкий график:
- Возможность начинать работу с 8:00 до 10:00
- Соответствующий сдвиг окончания рабочего дня
- Обязательное присутствие в офисе с 10:00 до 16:00

📝 Изменения в графике согласовываются с руководителем.
🏠 Возможность удаленной работы обсуждается индивидуально.''',
                    'category': 'рабочее время',
                    'tags': 'график, время, работа, офис, гибкий график'
                },
                {
                    'title': 'Корпоративные льготы и компенсации',
                    'content': '''Доступные льготы:

💼 ДМС (добровольное медицинское страхование)
🚗 Компенсация транспортных расходов
🍽️ Субсидированное питание в корпоративной столовой
📚 Компенсация обучения и профессиональных курсов
🏋️ Корпоративный фитнес
🎯 Программа лояльности с бонусами

Условия получения:
- Испытательный срок должен быть успешно пройден
- Стаж работы в компании от 3 месяцев
- Отсутствие дисциплинарных взысканий

📋 Подробности уточняйте в кадровой службе.''',
                    'category': 'льготы',
                    'tags': 'льготы, компенсации, ДМС, фитнес, обучение'
                },
                {
                    'title': 'Техническая поддержка и IT-оборудование',
                    'content': '''Для решения технических вопросов:

💻 Заявки на IT-поддержку подаются через корпоративную систему
📞 Телефон службы поддержки: доб. 100
🔧 Время работы поддержки: 9:00-18:00 в рабочие дни

Стандартное оборудование:
- Рабочий компьютер или ноутбук
- Монитор (по запросу второй)
- Клавиатура и мышь
- Корпоративный телефон (при необходимости)

⚠️ Личное использование корпоративного оборудования ограничено.
🔒 Обязательно соблюдение политики информационной безопасности.''',
                    'category': 'оборудование',
                    'tags': 'IT, компьютер, техника, поддержка, оборудование'
                }
            ]
            
            for article_data in default_articles:
                existing = KnowledgeBaseArticle.query.filter_by(
                    title=article_data['title']
                ).first()
                
                if not existing:
                    article = KnowledgeBaseArticle(**article_data)
                    db.session.add(article)
            
            db.session.commit()
            logging.info("Default knowledge base articles created")
            
        except Exception as e:
            logging.error(f"Error creating default articles: {str(e)}")
            db.session.rollback()
    
    def search_similar_questions(self, query: str, limit: int = 3) -> List[str]:
        """Поиск похожих вопросов для подсказок"""
        try:
            # Простой поиск по ключевым словам
            query_words = query.lower().split()
            similar_questions = []
            
            # Предопределенные частые вопросы
            common_questions = [
                "Как оформить отпуск?",
                "Что делать при болезни?",
                "Какой график работы?",
                "Какие есть льготы?",
                "Как получить справку?",
                "Где найти документы?",
                "Как связаться с HR?",
                "Когда выплачивается зарплата?",
                "Как оформить командировку?",
                "Что делать при опоздании?"
            ]
            
            for question in common_questions:
                question_words = question.lower().split()
                if any(word in question_words for word in query_words):
                    similar_questions.append(question)
                    if len(similar_questions) >= limit:
                        break
            
            return similar_questions
            
        except Exception as e:
            logging.error(f"Error searching similar questions: {str(e)}")
            return []
