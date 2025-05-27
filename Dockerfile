FROM python:3.9

EXPOSE 5002
WORKDIR /app
# Copy dependencies to cache the dependencies layer
COPY requirements.txt .
# Install the dependencies (from requirements.txt)
RUN pip install --no-cache-dir -r requirements.txt
# Ensure Flask is installed
RUN pip list | grep Flask
COPY . .
CMD ["python", "main.py"]