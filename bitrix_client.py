import os
import requests
import logging
from typing import Optional, Dict, Any


class BitrixClient:
    """Клиент для работы с Битрикс24 REST API"""
    
    def __init__(self):
        self.webhook_url = os.environ.get('BITRIX_WEBHOOK_URL', '')
        self.access_token = os.environ.get('BITRIX_ACCESS_TOKEN', '')
        self.base_url = os.environ.get('BITRIX_BASE_URL', '')
        
        if not any([self.webhook_url, self.access_token]):
            logging.warning("Bitrix credentials not found in environment variables")
    
    def send_message(self, chat_id: str, message: str) -> bool:
        """Отправка сообщения в чат Битрикс24"""
        try:
            if self.webhook_url:
                url = f"{self.webhook_url}/im.message.add"
            else:
                url = f"{self.base_url}/rest/{self.access_token}/im.message.add"
            
            data = {
                'DIALOG_ID': chat_id,
                'MESSAGE': message
            }
            
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get('result'):
                logging.info(f"Message sent successfully to chat {chat_id}")
                return True
            else:
                logging.error(f"Failed to send message: {result.get('error_description', 'Unknown error')}")
                return False
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Error sending message to Bitrix24: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error sending message: {str(e)}")
            return False
    
    def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Получение информации о пользователе"""
        try:
            if self.webhook_url:
                url = f"{self.webhook_url}/user.get"
            else:
                url = f"{self.base_url}/rest/{self.access_token}/user.get"
            
            data = {
                'ID': user_id
            }
            
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get('result'):
                return result['result'][0] if result['result'] else None
            else:
                logging.error(f"Failed to get user info: {result.get('error_description', 'Unknown error')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Error getting user info from Bitrix24: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error getting user info: {str(e)}")
            return None
    
    def get_chat_info(self, chat_id: str) -> Optional[Dict[str, Any]]:
        """Получение информации о чате"""
        try:
            if self.webhook_url:
                url = f"{self.webhook_url}/im.chat.get"
            else:
                url = f"{self.base_url}/rest/{self.access_token}/im.chat.get"
            
            data = {
                'CHAT_ID': chat_id
            }
            
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get('result'):
                return result['result']
            else:
                logging.error(f"Failed to get chat info: {result.get('error_description', 'Unknown error')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Error getting chat info from Bitrix24: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error getting chat info: {str(e)}")
            return None
    
    def set_bot_typing(self, chat_id: str) -> bool:
        """Установка статуса 'печатает' для бота"""
        try:
            if self.webhook_url:
                url = f"{self.webhook_url}/im.dialog.writing"
            else:
                url = f"{self.base_url}/rest/{self.access_token}/im.dialog.writing"
            
            data = {
                'DIALOG_ID': chat_id
            }
            
            response = requests.post(url, json=data, timeout=5)
            response.raise_for_status()
            
            return True
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Error setting typing status: {str(e)}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error setting typing status: {str(e)}")
            return False
    
    def get_department_info(self, department_id: str) -> Optional[Dict[str, Any]]:
        """Получение информации о подразделении"""
        try:
            if self.webhook_url:
                url = f"{self.webhook_url}/department.get"
            else:
                url = f"{self.base_url}/rest/{self.access_token}/department.get"
            
            data = {
                'ID': department_id
            }
            
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get('result'):
                return result['result'][0] if result['result'] else None
            else:
                logging.error(f"Failed to get department info: {result.get('error_description', 'Unknown error')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Error getting department info from Bitrix24: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error getting department info: {str(e)}")
            return None
    
    def create_task(self, title: str, description: str, responsible_id: str) -> Optional[str]:
        """Создание задачи в Битрикс24 для эскалации"""
        try:
            if self.webhook_url:
                url = f"{self.webhook_url}/tasks.task.add"
            else:
                url = f"{self.base_url}/rest/{self.access_token}/tasks.task.add"
            
            data = {
                'fields': {
                    'TITLE': title,
                    'DESCRIPTION': description,
                    'RESPONSIBLE_ID': responsible_id,
                    'PRIORITY': '2'  # Высокий приоритет
                }
            }
            
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            if result.get('result'):
                task_id = result['result']['task']['id']
                logging.info(f"Task created successfully with ID: {task_id}")
                return task_id
            else:
                logging.error(f"Failed to create task: {result.get('error_description', 'Unknown error')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Error creating task in Bitrix24: {str(e)}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error creating task: {str(e)}")
            return None
