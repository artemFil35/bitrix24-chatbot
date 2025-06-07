import os
import requests
import json
import logging
from typing import List, Dict, Optional


class YandexGPTClient:
    """Клиент для работы с YandexGPT API"""
    
    def __init__(self):
        self.api_key = os.environ.get('YANDEX_GPT_API_KEY', '')
        self.folder_id = os.environ.get('YANDEX_FOLDER_ID', 'ajetj6onsl7b25g8n0ji')
        self.model_uri = f"gpt://{self.folder_id}/yandexgpt-lite"
        self.base_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        
        if not self.api_key:
            logging.warning("YandexGPT API key not found in environment variables")
    
    def generate_response(self, user_message: str, context: Optional[List[Dict]] = None) -> str:
        """Генерация ответа с помощью YandexGPT"""
        try:
            if not self.api_key:
                return "Извините, сервис временно недоступен. Обратитесь к HR-специалисту."
            
            # Системный промпт для HR-бота
            system_prompt = """Вы - корпоративный HR-помощник для сотрудников компании. 
            
Ваша роль:
- Отвечайте на вопросы о HR-процедурах, отпусках, больничных, льготах
- Предоставляйте информацию о корпоративных политиках
- Помогайте с процедурными вопросами
- Говорите только на русском языке
- Будьте вежливы и профессиональны

Важные правила:
- Если вы не знаете точного ответа, честно скажите об этом
- При сложных вопросах рекомендуйте обратиться к HR-специалисту
- Не давайте правовых советов
- Не разглашайте конфиденциальную информацию о других сотрудниках
- Ответы должны быть краткими и по существу

Если спрашивают о чем-то, что не относится к HR или работе компании, вежливо перенаправьте разговор на рабочие темы."""

            # Формируем сообщения для API
            messages = [
                {
                    "role": "system",
                    "text": system_prompt
                }
            ]
            
            # Добавляем контекст предыдущих сообщений
            if context:
                for msg in context[-5:]:  # Берем только последние 5 сообщений
                    if msg.get('role') == 'user':
                        messages.append({
                            "role": "user",
                            "text": msg['content']
                        })
                    elif msg.get('role') == 'assistant':
                        messages.append({
                            "role": "assistant",
                            "text": msg['content']
                        })
            
            # Добавляем текущее сообщение пользователя
            messages.append({
                "role": "user",
                "text": user_message
            })
            
            # Подготавливаем запрос
            headers = {
                "Authorization": f"Api-Key {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "modelUri": self.model_uri,
                "completionOptions": {
                    "stream": False,
                    "temperature": 0.3,
                    "maxTokens": 2000
                },
                "messages": messages
            }
            
            # Отправляем запрос
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            response.raise_for_status()
            result = response.json()
            
            # Извлекаем ответ
            if 'result' in result and 'alternatives' in result['result']:
                alternatives = result['result']['alternatives']
                if alternatives and 'message' in alternatives[0]:
                    bot_response = alternatives[0]['message']['text']
                    logging.info(f"YandexGPT response generated successfully")
                    return bot_response
            
            logging.error(f"Unexpected response format: {result}")
            return "Извините, произошла ошибка при генерации ответа. Попробуйте переформулировать вопрос."
            
        except requests.exceptions.Timeout:
            logging.error("YandexGPT request timeout")
            return "Извините, сервис временно перегружен. Попробуйте повторить запрос через несколько секунд."
            
        except requests.exceptions.RequestException as e:
            logging.error(f"YandexGPT API error: {str(e)}")
            return "Извините, произошла ошибка связи с сервисом. Обратитесь к HR-специалисту."
            
        except Exception as e:
            logging.error(f"Unexpected error in YandexGPT client: {str(e)}")
            return "Извините, произошла техническая ошибка. Обратитесь к HR-специалисту."
    
    def check_content_safety(self, text: str) -> bool:
        """Проверка контента на безопасность (если доступно в API)"""
        try:
            # Базовая проверка на запрещенные слова
            forbidden_words = [
                'пароль', 'password', 'логин', 'login',
                'конфиденциально', 'секретно', 'зарплата других'
            ]
            
            text_lower = text.lower()
            for word in forbidden_words:
                if word in text_lower:
                    return False
            
            return True
            
        except Exception as e:
            logging.error(f"Error checking content safety: {str(e)}")
            return True  # По умолчанию разрешаем, если проверка не работает
    
    def generate_summary(self, conversation_messages: List[str]) -> str:
        """Генерация краткого резюме разговора"""
        try:
            if not self.api_key or not conversation_messages:
                return ""
            
            # Объединяем сообщения
            conversation_text = "\n".join(conversation_messages[-10:])  # Последние 10 сообщений
            
            summary_prompt = f"""Создайте краткое резюме следующего разговора с HR-ботом:

{conversation_text}

Резюме должно быть на русском языке и содержать:
- Основную тему вопроса
- Ключевые моменты обсуждения
- Результат консультации

Максимум 3-4 предложения."""

            messages = [
                {
                    "role": "user",
                    "text": summary_prompt
                }
            ]
            
            headers = {
                "Authorization": f"Api-Key {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "modelUri": self.model_uri,
                "completionOptions": {
                    "stream": False,
                    "temperature": 0.1,
                    "maxTokens": 500
                },
                "messages": messages
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=20
            )
            
            response.raise_for_status()
            result = response.json()
            
            if 'result' in result and 'alternatives' in result['result']:
                alternatives = result['result']['alternatives']
                if alternatives and 'message' in alternatives[0]:
                    return alternatives[0]['message']['text']
            
            return ""
            
        except Exception as e:
            logging.error(f"Error generating summary: {str(e)}")
            return ""
    
    def analyze_sentiment(self, text: str) -> str:
        """Анализ тональности сообщения"""
        try:
            # Простой анализ на основе ключевых слов
            positive_words = ['спасибо', 'хорошо', 'отлично', 'понятно', 'помогли']
            negative_words = ['плохо', 'не понятно', 'ошибка', 'проблема', 'не работает']
            
            text_lower = text.lower()
            
            positive_count = sum(1 for word in positive_words if word in text_lower)
            negative_count = sum(1 for word in negative_words if word in text_lower)
            
            if positive_count > negative_count:
                return "positive"
            elif negative_count > positive_count:
                return "negative"
            else:
                return "neutral"
                
        except Exception as e:
            logging.error(f"Error analyzing sentiment: {str(e)}")
            return "neutral"
