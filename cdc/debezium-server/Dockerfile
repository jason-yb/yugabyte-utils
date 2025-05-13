FROM openjdk:11-jdk-slim

# Install prerequisites
RUN apt-get update && apt-get install -y wget tar --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Download and extract Debezium Server
ARG DEBEZIUM_HOME=/opt/debezium-server
ARG DEBEZIUM_SERVER_VERSION=2.5.2.Final
ARG DEBEZIUM_SERVER_TGZ=debezium-server-dist-${DEBEZIUM_SERVER_VERSION}.tar.gz
ARG DEBEZIUM_SERVER_URL=https://repo1.maven.org/maven2/io/debezium/debezium-server-dist/${DEBEZIUM_SERVER_VERSION}/${DEBEZIUM_SERVER_TGZ}
RUN wget --progress=dot:giga ${DEBEZIUM_SERVER_URL} -O /tmp/${DEBEZIUM_SERVER_TGZ} && \
    mkdir -p ${DEBEZIUM_HOME} && \
    tar -xf /tmp/${DEBEZIUM_SERVER_TGZ} -C ${DEBEZIUM_HOME} --strip-components=1 && \
    rm /tmp/${DEBEZIUM_SERVER_TGZ}

# Set the working directory
WORKDIR ${DEBEZIUM_HOME}

# Remove vanilla Postgres connector to avoid classpath conflicts
RUN find lib -name 'debezium-connector-postgres-*' -delete

# Download and extract the YugabyteDB Connector
ARG DBZ_YB_CONNECTOR_VERSION=dz.2.5.2.yb.2024.2.3
ARG DBZ_YB_CONNECTOR_JAR=debezium-connector-yugabytedb-${DBZ_YB_CONNECTOR_VERSION}-jar-with-dependencies.jar
ARG DBZ_YB_CONNECTOR_URL=https://github.com/yugabyte/debezium/releases/download/${DBZ_YB_CONNECTOR_VERSION}/${DBZ_YB_CONNECTOR_JAR}
RUN wget --progress=dot:giga ${DBZ_YB_CONNECTOR_URL} -O lib/${DBZ_YB_CONNECTOR_JAR}

EXPOSE 8080
