FROM python:3.10-slim

WORKDIR /app

COPY bot.py requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 10000

CMD ["python", "bot.py"]
