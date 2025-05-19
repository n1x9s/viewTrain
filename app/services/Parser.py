import requests
from bs4 import BeautifulSoup
import openpyxl
import time

# 🟢 Генерируем список страниц с 1 по 11
page_urls = [f"https://easyoffer.ru/rating/golang_developer?page={i}" for i in range(1, 5)]

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
}

# Функция для получения списка вопросов на одной странице
def get_question_links(page_url):
    response = requests.get(page_url, headers=headers)
    if response.status_code != 200:
        print(f'❌ Ошибка {response.status_code}, не удалось загрузить {page_url}')
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    links = []

    for row in soup.select('td a'):
        question_text = row.text.strip()
        question_link = 'https://easyoffer.ru' + row['href']
        print(f'✅ Найден вопрос: {question_text} ({question_link})')
        links.append((question_text, question_link))

    return links

# Функция для получения ответа на вопрос
def get_answer(question_url):
    response = requests.get(question_url, headers=headers)
    if response.status_code != 200:
        print(f'❌ Ошибка {response.status_code}, не удалось загрузить {question_url}')
        return 'Ошибка загрузки'

    soup = BeautifulSoup(response.text, 'html.parser')

    # 🔍 Пробуем найти ответ в нескольких местах
    answer_selectors = ['.card-text', '.another-class', '.some-answer-class']
    answers = []

    for selector in answer_selectors:
        for answer_block in soup.select(selector):
            answers.append(answer_block.text.strip())

    final_answer = '\n\n'.join(answers) if answers else 'Ответ не найден'

    return final_answer

# Создаём Excel-файл
workbook = openpyxl.Workbook()
sheet = workbook.active
sheet.title = 'Python Interview Questions'
sheet.append(['Вопрос', 'Ссылка', 'Ответ'])

# 🔄 Проходим по каждой странице
for page_url in page_urls:
    print(f'🌍 Парсим страницу: {page_url}')
    questions = get_question_links(page_url)  # <--- Теперь передаём page_url правильно!

    if not questions:
        print(f'⚠️ На {page_url} вопросов не найдено!')
        continue

    # 🔄 Парсим каждый вопрос со страницы
    for question_text, question_link in questions:
        print(f'🔍 Парсим вопрос: {question_text}')
        answer = get_answer(question_link)

        sheet.append([question_text, question_link, answer])
        time.sleep(1)  # Делаем паузу, чтобы не забанили

# 💾 Сохраняем Excel-файл
file_name = 'Python_Interview_Questions.xlsx'
workbook.save(file_name)
print(f'✅ Данные сохранены в {file_name}')
