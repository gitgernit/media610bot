FROM python:3.11-slim

WORKDIR /
COPY . .
RUN python -m venv venv
RUN . venv/bin/activate
RUN pip install -r requirements/prod.txt
CMD ["python", "bot.py"]
