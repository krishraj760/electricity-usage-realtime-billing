# 1. Use an official, lightweight Python base image
FROM python:3.12-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file first to leverage Docker layer caching
COPY requirements.txt .

# 4. Install requirements without saving cache files to keep the image small
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the actual Python script into the container
COPY realtime_entso_electricity_pricing.py .

# 6. Run the script. ACI will automatically shut down when this process exits.
CMD ["python", "realtime_entso_electricity_pricing.py"]