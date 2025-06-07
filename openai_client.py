import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")

def ask_chatgpt(message):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты — корпоративный помощник. Отвечай понятно и лаконично."},
                {"role": "user", "content": message}
            ],
            temperature=0.7
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        return f"❗ Ошибка: {str(e)}"
