from python:3.10
add requirements.txt /tmp
run pip install -r /tmp/requirements.txt
add src /opt/src
WORKDIR /opt/src
RUN bash init.sh
RUN chmod 755 /opt/src/run.sh
CMD ["/opt/src/run.sh"]


