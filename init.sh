set -ex
REPOSITORY_DIRECTORY="${PWD}"
LIBRARIES="${REPOSITORY_DIRECTORY}/libraries"
SOURCE="${LIBRARIES}/source"

# Clean sbeacon-libraries
if [ -d "${LIBRARIES}" ]
  then
    rm -rf "${LIBRARIES}"
fi

mkdir "${LIBRARIES}"
mkdir "${SOURCE}"

#
# building lambda layers
#

# tabix
cd ${SOURCE}
wget https://github.com/samtools/htslib/releases/download/1.21/htslib-1.21.tar.bz2
tar -xf htslib-1.21.tar.bz2
cd htslib-1.21 && autoreconf && ./configure --enable-libcurl && make
cd ${REPOSITORY_DIRECTORY}
mkdir -p layers/binaries/lib
mkdir -p layers/binaries/bin
# TODO check what libraries are missing and add only those
ldd ${SOURCE}/htslib-1.21/tabix | awk 'NF == 4 { system("cp " $3 " ./layers/binaries/lib") }'
cp ${SOURCE}/htslib-1.21/tabix ./layers/binaries/bin/
ldd ${SOURCE}/htslib-1.21/bgzip | awk 'NF == 4 { system("cp " $3 " ./layers/binaries/lib") }'
cp ${SOURCE}/htslib-1.21/bgzip ./layers/binaries/bin/


# bcftools
cd ${SOURCE}
wget https://github.com/samtools/bcftools/releases/download/1.21/bcftools-1.21.tar.bz2
tar -xf bcftools-1.21.tar.bz2
cd bcftools-1.21 && autoreconf && ./configure && make
cd ${REPOSITORY_DIRECTORY}
mkdir -p layers/binaries/lib
mkdir -p layers/binaries/bin
ldd ${SOURCE}/bcftools-1.21/bcftools | awk 'NF == 4 { system("cp " $3 " ./layers/binaries/lib") }'
cp ${SOURCE}/bcftools-1.21/bcftools ./layers/binaries/bin/

# samtools
cd ${SOURCE}
git clone --recursive --depth 1 --branch develop https://github.com/samtools/samtools.git
cd samtools && autoreconf && ./configure --without-curses && make
cd ${REPOSITORY_DIRECTORY}
mkdir -p layers/binaries/lib
mkdir -p layers/binaries/bin
ldd ${SOURCE}/samtools/samtools | awk 'NF == 4 { system("cp " $3 " ./layers/binaries/lib") }'
cp ${SOURCE}/samtools/samtools ./layers/binaries/bin/

# gzip & gunzip
cd ${SOURCE}
wget http://ftp.gnu.org/gnu/gzip/gzip-1.12.tar.gz
tar -xzvf gzip-1.12.tar.gz && rm gzip-1.12.tar.gz
cd gzip-1.12 && ./configure && make && make install PREFIX=${REPOSITORY_DIRECTORY}/layers/binaries
cd ${REPOSITORY_DIRECTORY}
mkdir -p layers/binaries/lib
mkdir -p layers/binaries/bin
ldd ${SOURCE}/gzip-1.12/gzip | awk 'NF == 4 { system("cp " $3 " ./layers/binaries/lib") }'
cp ${SOURCE}/gzip-1.12/gzip ./layers/binaries/bin/
ldd ${SOURCE}/gzip-1.12/gunzip | awk 'NF == 4 { system("cp " $3 " ./layers/binaries/lib") }'
cp ${SOURCE}/gzip-1.12/gunzip ./layers/binaries/bin/

# python libraries layer
cd ${REPOSITORY_DIRECTORY}