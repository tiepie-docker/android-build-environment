FROM ubuntu:bionic

ENV DEBIAN_FRONTEND=noninteractive
ENV DEBCONF_NONINTERACTIVE_SEEN=true

ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

RUN apt-get update && \
    apt-get dist-upgrade -y && \
    apt-get install -y apt-utils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get install -y libice6 \
                       curl \
                       libsm6 \
                       lsb-release \
                       rsync \
                       git \
                       openssh-client \
                       make \
                       python-colorama \
                       flex \
                       unzip \
                       openjdk-8-jdk \
                       python \
                       python-numpy \
                       ca-certificates \
                       wget \
                       python3 \
                       git-lfs \
                       lib32stdc++6 \
                       libc6-dev-i386 \
                       lib32z1 \
                       bison \
                       php-cli \
                       iproute2 \
                       python-pep8 \
                       cmake && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV ANDROID_NDK_PATH=/opt/android-ndk-r15c
ENV ANDROID_NDK_ROOT=/opt/android-ndk-r15c
ENV ANDROID_SDK_PATH=/opt/android-sdk
ENV ANDROID_SDK_ROOT=/opt/android-sdk
ENV QT_PATH=/opt/Qt
ENV QT_VERSION=5.9.7

RUN wget -nv https://dl.google.com/android/repository/android-ndk-r15c-linux-x86_64.zip && \
    unzip -q android-ndk-r15c-linux-x86_64.zip -d /opt && \
    rm /android-ndk-r15c-linux-x86_64.zip 

RUN wget -nv https://dl.google.com/android/repository/sdk-tools-linux-3859397.zip && \
    mkdir -p /opt/android-sdk && \
    unzip -q sdk-tools-linux-3859397.zip -d /opt/android-sdk && \
    rm sdk-tools-linux-3859397.zip && \
    cd /opt/android-sdk/tools/bin && \
    yes | ./sdkmanager --licenses && \
    ./sdkmanager "tools" "platform-tools" "platforms;android-23" "build-tools;23.0.3"

RUN apt-get update && \
    apt-get dist-upgrade -y && \
    apt-get install -y g++ \
                       libfontconfig1 \
                       libdbus-1-3 \
                       libx11-xcb1 \
                       libnss3-dev \
                       libasound2-dev \
                       libxcomposite1 \
                       libxrender1 \
                       libxrandr2 \
                       libxcursor-dev \
                       libegl1-mesa-dev \
                       libxi-dev \
                       libxss-dev \
                       libxtst6 \
                       libgl1-mesa-dev \
                       libgl1-mesa-glx \
                       libglib2.0-0 \
                       libdbus-1-3 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN curl https://raw.githubusercontent.com/benlau/qtci/master/bin/extract-qt-installer > extract-qt-installer.sh && \
    chmod +x extract-qt-installer.sh && \
    wget -nv https://download.qt.io/archive/qt/5.9/5.9.7/qt-opensource-linux-x64-5.9.7.run && \
    chmod +x qt-opensource-linux-x64-5.9.7.run && \
    QT_CI_PACKAGES=qt.597.android_x86,qt.597.android_armv7 "$PWD"/extract-qt-installer.sh "$PWD"/qt-opensource-linux-x64-5.9.7.run "$QT_PATH" && \
    rm qt-opensource-linux-x64-5.9.7.run && \
    rm extract-qt-installer.sh && \
    ${QT_PATH}/5.9.7/android_armv7/src/3rdparty/gradle/gradlew -v && \
    ${QT_PATH}/5.9.7/android_armv7/src/3rdparty/gradle/gradlew --dry-run --refresh-dependencies -b ${QT_PATH}/5.9.7/android_armv7/src/android/templates/build.gradle | exit 0

RUN apt-get update && \
    apt-get dist-upgrade -y && \
    apt-get install -y g++ ruby-dev && \
    rm -rf /var/lib/apt/lists/* && \
    gem install fastlane -NV

