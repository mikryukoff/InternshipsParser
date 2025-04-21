import requests
import json
from time import sleep
from datetime import datetime

def get_internships():
    url = "https://api.hh.ru/vacancies"
    params = {
        "text": "стажер OR стажировка OR internship", 
        "area": 3,
        "per_page": 50,
        "page": 0,
        "experience": "noExperience"
    }
    
    all_vacancies = []
    
    try:
        while True:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            for item in data['items']:
                try:
                    vacancy_id = item['id']
                    vacancy_response = requests.get(f"{url}/{vacancy_id}")
                    vacancy_data = vacancy_response.json()
                    
                    description = vacancy_data.get('description', '')
                    
                    vacancy = {
                        'id': vacancy_id,
                        'name': item['name'],
                        'company': item['employer']['name'],
                        'salary': item.get('salary'),
                        'url': item['alternate_url'],
                        'published': item['published_at'],
                        'address': item['area']['name'],
                        'description': description,
                        'employment': item['employment']['name']
                    }
                    all_vacancies.append(vacancy)
                    
                except Exception as e:
                    print(f"Ошибка обработки вакансии {vacancy_id}: {str(e)}")
                    continue

            if params['page'] >= data['pages'] - 1:
                break
                
            params['page'] += 1
            sleep(0.3)

    except Exception as e:
        print(f"Ошибка: {str(e)}")
    
    filename = f"hh_internships_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_vacancies, f, ensure_ascii=False, indent=2)
        print(f"\nСохранено {len(all_vacancies)} вакансий с описаниями")
    except Exception as e:
        print(f"Ошибка сохранения: {str(e)}")

if __name__ == "__main__":
    get_internships()