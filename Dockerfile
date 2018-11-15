FROM ubuntu:16.04

# install dependencies from packages
RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -q -y \
        build-essential \
        wget \
        git \
        vim \
        libpq-dev \
	mysql-server \
        libmysqlclient-dev \
        python-dev \
	python-setuptools \
        python-pip \
        dialog \
        net-tools \
	nginx \
        cron

# clone the django site and rename folder
RUN git clone https://github.com/biobakery/jdrf1.git && \
    mv jdrf1/* jdrf1/.git* /usr/local/src/ && \
    rmdir jdrf1

# install python dependencies
RUN pip install --upgrade pip && \
    pip install setuptools && \
    pip install supervisor && \
    pip install django==1.11.0 gunicorn==19.7 MySQL-python==1.2.5 && \
    pip install django-widget-tweaks && \
    pip install fasteners && \
    pip install pronto && \
    pip install whoosh && \
    pip install pendulum

# add supervisor conf
RUN mkdir -pv /var/log/supervisord
ADD etc/supervisor.ini /etc/supervisord.conf

# replace nginx config to proxy gunicorn
RUN rm -v /etc/nginx/nginx.conf
ADD etc/jdrf_nginx.conf /etc/nginx/nginx.conf

# Add our crontab that will check for datasets to be released
ADD etc/crontab /etc/cron.d/jdrf-data-release-cron
RUN chmod 0644 /etc/cron.d/jdrf-data-release-cron
RUN crontab /etc/cron.d/jdrf-data-release-cron
RUN touch /var/log/cron.log

# install workflows dependencies
RUN pip install --no-cache-dir biobakery_workflows humann2 kneaddata

# install modules needed for validation
RUN pip install pandas && \
    pip install pathlib2 && \
    pip install typing && \
    pip install git+https://github.com/carze/PandasSchema.git && \
    pip install Jinja2 && \
    pip install openpyxl

# install java for kneaddata, numpy for metaphlan2, workflow visualization dependencies, and ldap
# remove texlive docs to save ~330 MB
# install matplotlib version that is compatible with hclust and biobakery workflows (latest version is not)
RUN apt-get update -y && \
    apt-get install -y apt-transport-https openjdk-8-jre python-numpy python-matplotlib \
        python-ldap libsasl2-dev libldap2-dev libssl-dev \
        python-scipy pandoc texlive software-properties-common \ 
        python-pandas python-biopython && \
    apt-get remove -y texlive-fonts-recommended-doc texlive-latex-base-doc \
        texlive-latex-recommended-doc \
        texlive-pictures-doc texlive-pstricks-doc && \
    pip install matplotlib==2.0.0

# install python ldap dependencies
RUN pip install django-auth-ldap

# install metaphlan2 and dependencies
RUN wget http://huttenhower.sph.harvard.edu/metaphlan2_downloads/metaphlan2-2.6.0.tar.gz && \
    tar xzvf metaphlan2-2.6.0.tar.gz && \
    mv biobakery-metaphlan2-c43e40a443ed/*.py /usr/local/bin/ && \
    mv biobakery-metaphlan2-c43e40a443ed/db_v20 /usr/local/bin/ && \
    mv biobakery-metaphlan2-c43e40a443ed/utils /usr/local/bin/ && \
    mv biobakery-metaphlan2-c43e40a443ed/strainphlan_src /usr/local/bin/ && \
    rm metaphlan2-2.6.0.tar.gz && \
    rm -r biobakery-metaphlan2-c43e40a443ed && \
    pip install biom-format

# Install the latest R
RUN add-apt-repository 'deb https://cloud.r-project.org/bin/linux/ubuntu xenial/' && \
    gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys E084DAB9 && \
    gpg -a --export E084DAB9 | apt-key add - && \
    apt-get update -y && \
    apt-get install r-base -y && \
    R -q -e "install.packages('vegan', repos='http://cran.r-project.org')"

# install hclust2
RUN wget https://bitbucket.org/nsegata/hclust2/get/3d589ab2cb68.tar.gz && \
    tar xzvf 3d589ab2cb68.tar.gz && \
    mv nsegata-hclust2-3d589ab2cb68/hclust2.py /usr/local/bin/ && \
    rm -r nsegata-hclust2-3d589ab2cb68/ && \
    rm 3d589ab2cb68.tar.gz

# install biobakery 16s dependencies (biom, clustalo, ea-utils, and picrust)
# rollback numpy version for h5py (to prevent future warning message in vis report with biom version)
RUN apt-get update -y && \
    apt-get install -y clustalo ea-utils && \
    pip install biom-format h5py==2.7.0 cogent==1.5.3 && \
    wget https://github.com/picrust/picrust/releases/download/v1.1.3/picrust-1.1.3.tar.gz && \
    tar -xzf picrust-1.1.3.tar.gz && \
    cd picrust-1.1.3 && \
    pip install . && \
    cd ../ && \
    rm -r picrust-1.1.3* && \
    download_picrust_files.py && \
    pip install numpy==1.13

# generate the whoosh indices we need for the autocomplete in some of the metadata 
# form fields
RUN python /usr/local/src/bin/create_ontology_index.py -i "http://purl.obolibrary.org/obo/envo.owl" \
    -o /opt/whoosh_ontology_indices/envo
RUN python /usr/local/src/bin/create_ontology_index.py -i "http://aber-owl.net/media/ontologies/BTO/33/bto.obo" \
    -o /opt/whoosh_ontology_indices/bto

EXPOSE :80
