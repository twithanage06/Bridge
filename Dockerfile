# 1. The Base Image: Start with a "pre-installed" Python environment
FROM python:3.10-slim

# 2. The Workspace: Create a folder inside the container where your app lives
WORKDIR /app

# 3. Dependencies: Copy just the requirements file first (for faster building)
COPY requirements.txt .

# 4. Install: Download the libraries listed in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy Code: Move your app.py and other files into the container
COPY . .

# 6. Communication: Tell Docker that the app will listen on port 5000
EXPOSE 5000

# 7. Start: The command to run when the container turns on
CMD ["python", "app.py"]