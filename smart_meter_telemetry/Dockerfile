# 1. Use an official, lightweight Python base image
FROM python:3.12-slim

# 2. Force Python to flush logs instantly (critical for 24/7 Azure monitoring)
ENV PYTHONUNBUFFERED=1

# 3. Set the working directory
WORKDIR /app

# 4. Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the 24/7 Python script
COPY simulated_smart_meter_telemetry.py .

# 6. Run the script continuously
CMD ["python", "simulated_smart_meter_telemetry.py"]