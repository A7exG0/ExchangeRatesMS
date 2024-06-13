from fastapi import FastAPI, HTTPException, Response
import requests
import binascii
import json
import logging
from datetime import datetime, timedelta

app = FastAPI()

cached_data = {}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_rates(date: str):
    """
    Возвращает курсы валют по указанной дате. При отсутствии данных по указанной дате, дополнительно сохраняет эти
    данные в кэш. 
    """
    global cached_data

    # Проверка формата даты
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    logger.info(f"\tLoading exchange rates for date: {date}")

    # Проверка, загружены ли курсы валют за данную дату
    if date in cached_data: 
        return cached_data[date]

    url = f"https://www.nbrb.by/api/exrates/rates?ondate={date}&periodicity=0"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверка статуса ответа
        data = response.json()

        # Проверка наличия данных в ответе
        if not data:
            raise HTTPException(status_code=404, detail="No data available for the given date.")
        
        # Добавление в память нового значения курсов валют
        cached_data[date] = data

        return data

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")

def make_responce(body: dict):
    """
    Создает ответ. Добавляет заголовок CRC32.
    """
    
    body_json = json.dumps(body, ensure_ascii=False)
    body_bytes = body_json.encode('utf-8')

    # Вычисление CRC32
    body_crc = binascii.crc32(body_bytes) & 0xffffffff

    response = Response(content=body_json, media_type="application/json; charset=utf-8")
    
    # Добавление заголовка CRC32
    response.headers["CRC32"] = str(body_crc)

    return response

def calculate_rate_change(date_str: str, rate):
    """
    Высчитывает разницу курсов валют по выбранной дате и предыдущей. 
    """
    date = datetime.strptime(date_str, "%Y-%m-%d")
    previous_date = date - timedelta(days=1)
    previous_date_str = previous_date.strftime("%Y-%m-%d")

    data_previous_date = load_rates(previous_date_str)

    for previous_rate in data_previous_date:
        if str(rate["Cur_ID"]) == str(previous_rate["Cur_ID"]):
            return rate["Cur_OfficialRate"] - previous_rate["Cur_OfficialRate"]
        
    return "Not found"

@app.get("/check")
def check(date: str):
    """
    Первый endpoint по условию. Получает курсы валют банка по указанной дате.
    Отображает сообщение о статусе выполнения.
    """
    data = load_rates(date)

    response_body = {
            "date": date,
            "status": "Success",
            "message": "Exchange rates loaded successfully.",
            "data": data
        }

    return make_responce(response_body)

@app.get("/get_rate")
def get_rate(date: str, code: str):
    """
    Второй endpoint по условию. Возвращает курсы валют по указанной дате и по указанному коду валют.
    Дополнительно выводит разницу между курсами данной даты и предыдущей. 
    """
    data = load_rates(date)
    for rate in data:
        if str(rate["Cur_ID"]) == code:
            rate['change'] = calculate_rate_change(date, rate)
            return make_responce(rate)
        
    raise HTTPException(status_code=404, detail="Code not found")
    