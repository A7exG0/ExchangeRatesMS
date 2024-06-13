from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse
import requests
from datetime import datetime
import binascii
import json

app = FastAPI()

def load_rates(date):
    # Проверка формата даты
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    url = f"https://www.nbrb.by/api/exrates/rates?ondate={date}&periodicity=0"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Проверка статуса ответа
        data = response.json()

        # Проверка наличия данных
        if not data:
            raise HTTPException(status_code=404, detail="No data available for the given date.")
        
        return data

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")

def make_responce(body: dict):
    # Вычисление CRC32
    body_json = json.dumps(body, ensure_ascii=False)
    body_bytes = body_json.encode('utf-8')
    body_crc = binascii.crc32(body_bytes) & 0xffffffff

    # Создание объекта Response
    response = Response(content=body_json, media_type="application/json; charset=utf-8")
    
    # Добавление заголовка CRC32
    response.headers["CRC32"] = str(body_crc)

    return response

@app.get("/check")
def check(date: str):
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
    data = load_rates(date)
    for rate in data:
        if str(rate["Cur_ID"]) == code:
            return make_responce(rate)
        
    raise HTTPException(status_code=404, detail="Code not found")