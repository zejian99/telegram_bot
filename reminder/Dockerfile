# Use an official Python runtime as a base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /reminder

# Copy the current directory contents into the container at /app
COPY . /reminder

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8888 available to the world outside this container
EXPOSE 8889 

# Define environment variable
ENV PORT 8889

# Run bot.py when the container launches
CMD ["python", "reminder.py"]