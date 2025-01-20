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
git clone --recursive --depth 1 --branch develop https://github.com/samtools/htslib.git 
cd htslib && autoreconf && ./configure --enable-libcurl && make
cd ${REPOSITORY_DIRECTORY}
mkdir -p layers/binaries/lib
mkdir -p layers/binaries/bin
# TODO check what libraries are missing and add only those
ldd ${SOURCE}/htslib/tabix | awk 'NF == 4 { system("cp " $3 " ./layers/binaries/lib") }'
cp ${SOURCE}/htslib/tabix ./layers/binaries/bin/
ldd ${SOURCE}/htslib/bgzip | awk 'NF == 4 { system("cp " $3 " ./layers/binaries/lib") }'
cp ${SOURCE}/htslib/bgzip ./layers/binaries/bin/


# bcftools
cd ${SOURCE}
git clone --recursive --depth 1 --branch develop https://github.com/samtools/bcftools.git
cd bcftools && autoreconf && ./configure && make
cd ${REPOSITORY_DIRECTORY}
mkdir -p layers/binaries/lib
mkdir -p layers/binaries/bin
ldd ${SOURCE}/bcftools/bcftools | awk 'NF == 4 { system("cp " $3 " ./layers/binaries/lib") }'
cp ${SOURCE}/bcftools/bcftools ./layers/binaries/bin/

# samtools
cd ${SOURCE}
git clone --recursive --depth 1 --branch develop https://github.com/samtools/samtools.git
cd samtools && autoheader && autoconf -Wno-syntax && ./configure --without-curses && make
cd ${REPOSITORY_DIRECTORY}
mkdir -p layers/binaries/lib
mkdir -p layers/binaries/bin
ldd ${SOURCE}/samtools/samtools | awk 'NF == 4 { system("cp " $3 " ./layers/binaries/lib") }'
cp ${SOURCE}/samtools/samtools ./layers/binaries/bin

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