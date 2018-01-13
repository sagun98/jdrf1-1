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
	nginx

# clone the django site and rename folder
RUN git clone https://github.com/biobakery/jdrf1.git && \
    mv jdrf1/* jdrf1/.git* /usr/local/src/ && \
    rmdir jdrf1

# install python dependencies
RUN pip install --upgrade pip && \
    pip install setuptools && \
    pip install supervisor && \
    pip install django==1.11.0 gunicorn==19.7 MySQL-python==1.2.5

# add supervisor conf
RUN mkdir -pv /var/log/supervisord
ADD etc/supervisor.ini /etc/supervisord.conf

# replace nginx config to proxy gunicorn
RUN rm -v /etc/nginx/nginx.conf
ADD etc/jdrf_nginx.conf /etc/nginx/nginx.conf

# install workflows dependencies
RUN pip install --no-cache-dir biobakery_workflows humann2 kneaddata

# install java for kneaddata
RUN apt-get install -y openjdk-8-jre

# install metaphlan2 and dependencies
RUN apt-get install -y python-numpy
RUN wget http://huttenhower.sph.harvard.edu/metaphlan2_downloads/metaphlan2-2.6.0.tar.gz && \
    tar xzvf metaphlan2-2.6.0.tar.gz && \
    mv biobakery-metaphlan2-c43e40a443ed/*.py /usr/local/bin/ && \
    mv biobakery-metaphlan2-c43e40a443ed/db_v20 /usr/local/bin/ && \
    mv biobakery-metaphlan2-c43e40a443ed/utils /usr/local/bin/ && \
    mv biobakery-metaphlan2-c43e40a443ed/strainphlan_src /usr/local/bin/ && \
    rm metaphlan2-2.6.0.tar.gz && \
    rm -r biobakery-metaphlan2-c43e40a443ed

# install workflow visualizations dependencies
RUN apt-get install python-matplotlib python-scipy pandoc texlive software-properties-common python-pandas python-biopython -y
# remove texlive docs to save ~330 MB
RUN apt-get install texlive -y && \
    apt-get remove texlive-fonts-recommended-doc texlive-latex-base-doc texlive-latex-recommended-doc texlive-pictures-doc texlive-pstricks-doc

# Install the latest R
RUN add-apt-repository 'deb https://cloud.r-project.org/bin/linux/ubuntu xenial/'
RUN gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys E084DAB9
RUN gpg -a --export E084DAB9 | apt-key add -
RUN apt-get -qq update && apt-get install r-base -y
RUN R -q -e "install.packages('vegan', repos='http://cran.r-project.org')"

# install hclust2
RUN wget https://bitbucket.org/nsegata/hclust2/get/3d589ab2cb68.tar.gz && \
    tar xzvf 3d589ab2cb68.tar.gz && \
    mv nsegata-hclust2-3d589ab2cb68/hclust2.py /usr/local/bin/ && \
    rm -r nsegata-hclust2-3d589ab2cb68/ && \
    rm 3d589ab2cb68.tar.gz

# install ldap dependencies
RUN apt-get install python-ldap -y
RUN pip install django-auth-ldap

EXPOSE :80
