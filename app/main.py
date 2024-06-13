from fastapi import FastAPI, HTTPException
import requests
from datetime import datetime

app = FastAPI()

@app.get("/check")
def check(date: str):
    
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

        return {
            "date": date,
            "status": "Success",
            "message": "Exchange rates loaded successfully."
        }
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error loading data: {str(e)}")
