FROM continuumio/anaconda
# Set up conda
ENV ANACONDA_HOME /opt/conda
RUN conda update --name base conda
RUN $ANACONDA_HOME/bin/conda install -y 'pyqt<5' configargparse
RUN apt-get install -y fontconfig
# Copy the current directory contents into the container at /app
COPY . /app
# Set the working directory to /app
WORKDIR app
# Run app.py when the container launches
CMD ["python", "TestStucture.py"]

