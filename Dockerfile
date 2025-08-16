FROM python:3.12.11-alpine3.21

# Install system dependencies including nano
RUN apk update && apk add --no-cache 

# Set working directory
WORKDIR /app

# Copy dependencies and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app
COPY . .

# Run the application
CMD ["python", "app/main.py" ]

