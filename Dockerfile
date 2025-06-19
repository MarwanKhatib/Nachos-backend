FROM python:3.12.3-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x dev-start.sh

CMD ["/bin/bash", "dev-start.sh"]
