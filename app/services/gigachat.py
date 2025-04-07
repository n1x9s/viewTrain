from gigachat import GigaChat
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class GigaChatService:
    def __init__(self):
        self.client = GigaChat(
            credentials=settings.GIGACHAT_CREDENTIALS,
            verify_ssl_certs=False  # Отключаем проверку SSL-сертификата
        )
    
    async def evaluate_answer(self, question: str, user_answer: str) -> tuple[float, str]:
        """
        Оценить ответ пользователя с помощью GigaChat
        
        Args:
            question: Текст вопроса
            user_answer: Ответ пользователя
            
        Returns:
            tuple[float, str]: Оценка (от 0 до 1) и обратная связь
        """
        try:
            # Проверяем, не пустой ли ответ
            if not user_answer or user_answer.strip() == "":
                return 0.0, "Вы не предоставили ответ на вопрос. Пожалуйста, попробуйте ответить еще раз."
            
            # Проверяем ответы типа "не знаю"
            not_know_phrases = ["не знаю", "не помню", "не уверен", "затрудняюсь ответить", "не могу ответить"]
            if any(phrase in user_answer.lower() for phrase in not_know_phrases):
                # Генерируем правильный ответ
                correct_answer_prompt = f"""
                Ты - опытный Python-разработчик и интервьюер. 
                Дай развернутый и правильный ответ на следующий вопрос интервью:
                
                Вопрос: {question}
                
                Требования к ответу:
                1. Ответ должен быть полным и точным
                2. Используй профессиональную терминологию
                3. Приведи примеры кода, если это уместно
                4. Объясни сложные концепции простым языком
                5. Укажи практическое применение
                6. Не добавляй дату и источник
                7. Давай только чистый текст без дополнительных метаданных
                """
                
                correct_answer_response = self.client.chat(correct_answer_prompt)
                correct_answer = correct_answer_response.choices[0].message.content
                return 0.0, f"Правильный ответ:\n{correct_answer}"
            
            prompt = f"""
            Ты - строгий экзаменатор по Python. Оцени ответ пользователя на вопрос интервью.
            
            Вопрос: {question}
            Ответ пользователя: {user_answer}
            
            Сначала сгенерируй правильный ответ на вопрос, а затем оцени ответ пользователя.
            
            Критерии оценки:
            1. Если ответ пустой или не содержит полезной информации - оценка 0
            2. Если ответ содержит только общие фразы без конкретики - оценка 0
            3. Если ответ частично верный, но неполный - оценка 0.3-0.4
            4. Если ответ верный, но с неточностями - оценка 0.5-0.7
            5. Если ответ полностью верный - оценка 0.8-1.0
            
            Дополнительные критерии оценки:
            - Техническая точность: насколько точно описаны технические детали
            - Полнота ответа: охвачены ли все важные аспекты вопроса
            - Структура ответа: логичность и последовательность изложения
            - Примеры и иллюстрации: наличие конкретных примеров кода или аналогий
            - Терминология: правильное использование профессиональной терминологии
            
            Верни ответ в формате JSON:
            {{
                "score": число от 0 до 1,
                "feedback": "подробный комментарий к ответу с указанием, что именно было неверно или неполно",
                "recommendations": [
                    "конкретные рекомендации по улучшению ответа",
                    "что именно нужно добавить или исправить",
                    "какие аспекты были упущены"
                ],
                "strengths": [
                    "сильные стороны ответа",
                    "что было сделано хорошо"
                ],
                "weaknesses": [
                    "слабые стороны ответа",
                    "что нужно улучшить"
                ],
                "correct_answer": "развернутый правильный ответ на вопрос"
            }}
            
            Важно:
            1. Будь строг в оценке. Ответ "не знаю" или "не помню" должен получить оценку 0
            2. Предоставляй конкретные рекомендации по улучшению
            3. Указывай как сильные, так и слабые стороны ответа
            4. Если в ответе есть код, проверь его на корректность и соответствие лучшим практикам
            5. Обрати внимание на использование правильной терминологии
            6. Проверь, все ли важные аспекты вопроса были затронуты
            7. Не добавляй дату и источник в ответ
            8. Не используй форматирование типа "ИсточникРекомендации:"
            9. Давай только чистый текст без дополнительных метаданных
            """
            
            response = self.client.chat(prompt)
            result = response.choices[0].message.content
            
            # Проверяем, не пустой ли ответ от GigaChat
            if not result or result.strip() == "":
                logger.error("Получен пустой ответ от GigaChat")
                return 0.0, "Не удалось оценить ответ. Пожалуйста, попробуйте еще раз."
            
            # Очищаем ответ от markdown-форматирования
            result = result.strip()
            if result.startswith("```json"):
                result = result[7:]  # Удаляем ```json
            if result.endswith("```"):
                result = result[:-3]  # Удаляем ```
            result = result.strip()
            
            # Парсим JSON из ответа
            import json
            try:
                evaluation = json.loads(result)
            except json.JSONDecodeError as e:
                logger.error(f"Ошибка парсинга JSON от GigaChat: {str(e)}, ответ: {result}")
                return 0.0, "Не удалось обработать ответ. Пожалуйста, попробуйте еще раз."
            
            # Проверяем наличие необходимых полей
            required_fields = ["score", "feedback", "recommendations", "strengths", "weaknesses", "correct_answer"]
            if not all(key in evaluation for key in required_fields):
                logger.error(f"Некорректный формат ответа от GigaChat: {evaluation}")
                return 0.0, "Не удалось оценить ответ. Пожалуйста, попробуйте еще раз."
            
            # Формируем полный фидбэк
            feedback = f"{evaluation['feedback']}\n\n"
            feedback += "Сильные стороны:\n" + "\n".join(f"- {s}" for s in evaluation['strengths']) + "\n\n"
            feedback += "Что нужно улучшить:\n" + "\n".join(f"- {w}" for w in evaluation['weaknesses']) + "\n\n"

            feedback += "Рекомендации:\n" + "\n".join(f"- {r}" for r in evaluation['recommendations']) + "\n\n"

            feedback += "Правильный ответ:\n" + evaluation['correct_answer']

            feedback += "Правильный ответ:\n" + correct_answer
            feedback += "Рекомендации:\n" + "\n".join(f"- {r}" for r in evaluation['recommendations'])

            
            return evaluation["score"], feedback
            
        except Exception as e:
            logger.error(f"Ошибка при оценке ответа через GigaChat: {str(e)}")
            # В случае ошибки возвращаем базовую оценку
            return 0.0, "Не удалось оценить ответ автоматически. Пожалуйста, попробуйте еще раз."


# Создаем глобальный экземпляр сервиса
gigachat_service = GigaChatService() 