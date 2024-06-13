from fastapi import FastAPI, HTTPException
import requests
from datetime import datetime

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

@app.get("/check")
def check(date: str):
    load_rates(date)

    return {
            "date": date,
            "status": "Success",
            "message": "Exchange rates loaded successfully."
        }

@app.get("/get_rate")
def get_rate(date: str, code: str):
    data = load_rates(date)

    for rate in data:
        if str(rate["Cur_ID"]) == code:
            return rate
    raise HTTPException(status_code=404, detail="Code not found")