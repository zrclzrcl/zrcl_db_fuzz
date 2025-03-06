# syntax=docker/dockerfile:1.2
from ubuntu:22.04
LABEL maintainer="Squirrel"

# common config
RUN apt-get update
RUN apt-get -y install make cmake build-essential vim sudo git openssh-client\
    clang ninja-build pkg-config clang-format libpq-dev llvm libyaml-cpp-dev zlib1g-dev \
    libreadline8 libreadline-dev bison flex python3-fire

RUN mkdir -p /home && \
    groupadd dobigthing && \
    useradd -l -K UMASK=0000 -d /home -g dobigthing dobigthing && \
    chown dobigthing:dobigthing /home

RUN	echo "dobigthing:dobigthing" | chpasswd && usermod -a -G sudo dobigthing
RUN chmod +w /etc/sudoers && \
    echo "%dobigthing   ALL=(ALL:ALL)NOPASSWD:ALL" >> /etc/sudoers && \
    chmod -w /etc/sudoers

USER dobigthing
WORKDIR /home
RUN mkdir -p -m 0700 ~/.ssh && \
    ssh-keyscan github.com >> ~/.ssh/known_hosts

RUN --mount=type=ssh git clone git@github.com:zrclzrcl/zrcl_db_fuzz.git  &&  \
    cd zrcl_db_fuzz && git submodule update --init && \
    cd Squirrel && git submodule update --init && \
    cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DPOSTGRESQL=ON && \
    cmake --build build -j && \
    cd AFLplusplus/ && LLVM_CONFIG=llvm-config-14 make -j20

RUN git clone --depth=1 https://github.com/postgres/postgres.git postgres/ && \
    mkdir bld/ && cd bld/ && \
    CC=/home/zrcl_db_fuzz/Squirrel/AFLplusplus/afl-cc CXX=/home/zrcl_db_fuzz/Squirrel/AFLplusplus/afl-c++ \
    ../postgres/configure

RUN cd bld/ && make -j && sudo make install &&  \
    sudo mkdir /usr/local/pgsql/data && sudo chown dobigthing /usr/local/pgsql/data &&  \
    AFL_IGNORE_PROBLEMS=1 /usr/local/pgsql/bin/initdb -D /usr/local/pgsql/data

RUN AFL_DEBUG=1 __AFL_SHM_ID=1234 /usr/local/pgsql/bin/postgres 2>&1 | grep "__afl_map_size" | tail -n 1 | cut -d"," -f8 | cut -d" " -f 3 > /tmp/mapsize
ADD postgre_BGSeed/  /home/zrcl_db_fuzz/Squirrel/data/fuzz_root/postgre_BGSeed/
WORKDIR /home/zrcl_db_fuzz/Squirrel/scripts/utils
ENTRYPOINT AFL_MAP_SIZE=$(cat /tmp/mapsize) python3 run.py postgresql ../../data/fuzz_root/postgre_BGSeed/