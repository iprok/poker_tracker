# Use the official Python image
FROM python:3.9

# Set the working directory
WORKDIR /app

# Copy project files into the container
COPY . .

# Install dependencies (if you have a requirements.txt)
RUN pip install -r requirements.txt
RUN pip install git+https://github.com/psf/black

# Specify the default command to run your Python app
CMD ["python", "bot_main.py"]
