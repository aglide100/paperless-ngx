FROM ghcr.io/paperless-ngx/paperless-ngx:latest

RUN apt update && \
    apt install -y \
    xsltproc \
    libxml2-utils \
    wkhtmltopdf \
    fonts-noto-cjk fonts-nanum* fonts-unfonts-core fonts-unfonts-extra fonts-baekmuk && \  
    apt clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install pyhwp lxml pdfkit pyhtml2pdf  beautifulsoup4 

ENV XDG_RUNTIME_DIR=/tmp/runtime-paperless
RUN mkdir -p /tmp/runtime-paperless && \
    chown 1000:1000 /tmp/runtime-paperless && \
    chmod 0700 /tmp/runtime-paperless

COPY ./src/paperless/settings.py /usr/src/paperless/src/paperless/settings.py

COPY ./src/paperless_hwp/ /usr/src/paperless/src/paperless_hwp/
