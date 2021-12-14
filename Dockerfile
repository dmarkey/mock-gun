from alpine:3.15
run apk add py3-pip tzdata
add requirements.txt /tmp
run pip install -r /tmp/requirements.txt
add src /opt/src
WORKDIR /opt/src
RUN chmod 755 /opt/src/run.sh
CMD ["/opt/src/run.sh"]


