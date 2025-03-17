import aiohttp
from typing import Tuple
import json
from app.core.config import settings


class GigaChatService:
    def __init__(self):
        self.auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        self.api_url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
        self.scope = "GIGACHAT_API_PERS"
        self._token = None
        
        # Получаем креды из настроек
        self.client_id = settings.gigachat_client_id
        self.client_secret = settings.gigachat_client_secret
    
    async def _get_token(self) -> str:
        """Получить токен для доступа к API"""
        async with aiohttp.ClientSession() as session:
            auth = aiohttp.BasicAuth(self.client_id, self.client_secret)
            data = {"scope": self.scope}
            
            async with session.post(self.auth_url, auth=auth, data=data, ssl=False) as response:
                if response.status != 200:
                    raise Exception(f"Ошибка получения токена: {await response.text()}")
                
                result = await response.json()
                return result["access_token"]
    
    async def evaluate_answer(self, question: str, correct_answer: str, user_answer: str) -> Tuple[float, str]:
        """Оценить ответ пользователя с помощью GigaChat"""
        if not self._token:
            self._token = await self._get_token()
        
        prompt = f"""Ты - система оценки ответов на вопросы по программированию. 
        
Вопрос: {question}
Правильный ответ: {correct_answer}
Ответ пользователя: {user_answer}

Оцени ответ пользователя по шкале от 0 до 1, где:
0 - полностью неверный ответ
1 - полностью верный ответ

Также дай развернутую обратную связь о том, что было правильно, а что можно улучшить.

Ответ дай в формате JSON:
{{
    "score": float,  // оценка от 0 до 1
    "feedback": string  // обратная связь
}}"""

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self._token}"
        }
        
        data = {
            "model": "GigaChat:latest",
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.1
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.api_url, headers=headers, json=data, ssl=False) as response:
                if response.status != 200:
                    # Если токен истек, пробуем получить новый
                    if response.status == 401:
                        self._token = await self._get_token()
                        headers["Authorization"] = f"Bearer {self._token}"
                        async with session.post(self.api_url, headers=headers, json=data, ssl=False) as retry_response:
                            if retry_response.status != 200:
                                raise Exception(f"Ошибка оценки ответа: {await retry_response.text()}")
                            result = await retry_response.json()
                    else:
                        raise Exception(f"Ошибка оценки ответа: {await response.text()}")
                else:
                    result = await response.json()
                
                try:
                    response_text = result["choices"][0]["message"]["content"]
                    evaluation = json.loads(response_text)
                    return evaluation["score"], evaluation["feedback"]
                except (KeyError, json.JSONDecodeError) as e:
                    raise Exception(f"Ошибка парсинга ответа от GigaChat: {str(e)}")


# Создаем глобальный экземпляр сервиса
gigachat_service = GigaChatService() 