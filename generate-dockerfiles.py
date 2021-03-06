from __future__ import print_function
import os
import sys
import json

ANDROID_NDK_VERSION = "r20b"

QT_MAJOR_VERISON = 5
QT_MINOR_VERISON = 14
QT_RELEASE_VERISON = 0

try:
    for suite in ["bionic"]:
        if not os.path.exists(suite):
            os.mkdir(suite)

        # Read packages.json:
        packages = []
        with open("packages.json") as f:
            data = json.load(f)
            if "all" in data:
                packages += data["all"]
            if suite in data:
                packages += data[suite]
            packages = list(set(packages))

        docker_file = open(suite + "/Dockerfile", "w")
        docker_file.write("FROM ubuntu:" + suite + "\n")
        docker_file.write("\n")

        docker_file.write("ENV DEBIAN_FRONTEND=noninteractive\n")
        docker_file.write("ENV DEBCONF_NONINTERACTIVE_SEEN=true\n")
        docker_file.write("\n")

        # Needed for fastlane:
        docker_file.write("ENV LANG C.UTF-8\n")
        docker_file.write("ENV LC_ALL C.UTF-8\n")
        docker_file.write("\n")

        docker_file.write("RUN apt-get update && \\\n")
        docker_file.write("    apt-get install -y apt-utils && \\\n")
        docker_file.write("    apt-get clean && \\\n")
        docker_file.write("    rm -rf /var/lib/apt/lists/*\n")
        docker_file.write("\n")

        if packages:
            docker_file.write("RUN apt-get update && \\\n")
            docker_file.write("    apt-get install -y " + (" \\\n" + " " * 23).join(packages) + " && \\\n")
            docker_file.write("    apt-get clean && \\\n")
            docker_file.write("    rm -rf /var/lib/apt/lists/*\n")
            docker_file.write("\n")

        if suite == "xenial":
            docker_file.write("RUN wget -nv --content-disposition https://packagecloud.io/github/git-lfs/packages/ubuntu/xenial/git-lfs_2.3.4_amd64.deb/download.deb && \\\n")
            docker_file.write("    dpkg -i git-lfs_2.3.4_amd64.deb && \\\n")
            docker_file.write("    rm git-lfs_2.3.4_amd64.deb\n")
            docker_file.write("\n")

        docker_file.write("ENV ANDROID_NDK_PATH=/opt/android-ndk-" + ANDROID_NDK_VERSION + "\n")
        docker_file.write("ENV ANDROID_NDK_ROOT=/opt/android-ndk-" + ANDROID_NDK_VERSION + "\n")
        docker_file.write("ENV ANDROID_SDK_PATH=/opt/android-sdk\n")
        docker_file.write("ENV ANDROID_SDK_ROOT=/opt/android-sdk\n")
        docker_file.write("ENV QT_PATH=/opt/Qt\n")
        docker_file.write("ENV QT_VERSION=" + str(QT_MAJOR_VERISON) + "." + str(QT_MINOR_VERISON) + "." + str(QT_RELEASE_VERISON) + "\n")
        docker_file.write("\n")

        docker_file.write("RUN wget -nv https://dl.google.com/android/repository/android-ndk-" + ANDROID_NDK_VERSION + "-linux-x86_64.zip && \\\n")
        docker_file.write("    unzip -q android-ndk-" + ANDROID_NDK_VERSION + "-linux-x86_64.zip -d /opt && \\\n")
        docker_file.write("    rm /android-ndk-" + ANDROID_NDK_VERSION + "-linux-x86_64.zip\n")
        docker_file.write("\n")

        docker_file.write("RUN wget -nv https://dl.google.com/android/repository/sdk-tools-linux-4333796.zip && \\\n")
        docker_file.write("    mkdir -p /opt/android-sdk && \\\n")
        docker_file.write("    unzip -q sdk-tools-linux-4333796.zip -d /opt/android-sdk && \\\n")
        docker_file.write("    rm sdk-tools-linux-4333796.zip && \\\n")
        docker_file.write("    cd /opt/android-sdk/tools/bin && \\\n")
        docker_file.write("    yes | ./sdkmanager --licenses && \\\n")
        docker_file.write("    ./sdkmanager \"tools\" \"platform-tools\" \"platforms;android-25\" \"build-tools;25.0.3\"\n")
        docker_file.write("\n")

        # Depenencies for Qt installer:
        docker_file.write("RUN apt-get update && \\\n")
        docker_file.write("    apt-get install -y g++ \\\n")
        docker_file.write("                       libfontconfig1 \\\n")
        docker_file.write("                       libdbus-1-3 \\\n")
        docker_file.write("                       libx11-xcb1 \\\n")
        docker_file.write("                       libnss3-dev \\\n")
        docker_file.write("                       libasound2-dev \\\n")
        docker_file.write("                       libxcomposite1 \\\n")
        docker_file.write("                       libxrender1 \\\n")
        docker_file.write("                       libxrandr2 \\\n")
        docker_file.write("                       libxcursor-dev \\\n")
        docker_file.write("                       libegl1-mesa-dev \\\n")
        docker_file.write("                       libxi-dev \\\n")
        docker_file.write("                       libxss-dev \\\n")
        docker_file.write("                       libxtst6 \\\n")
        docker_file.write("                       libgl1-mesa-dev \\\n")
        docker_file.write("                       libgl1-mesa-glx \\\n")
        docker_file.write("                       libglib2.0-0 \\\n")
        docker_file.write("                       libdbus-1-3 && \\\n")
        docker_file.write("    apt-get clean && \\\n")
        docker_file.write("    rm -rf /var/lib/apt/lists/*\n")
        docker_file.write("\n")

        docker_file.write("RUN curl https://raw.githubusercontent.com/benlau/qtci/master/bin/extract-qt-installer > extract-qt-installer.sh && \\\n")
        docker_file.write("    chmod +x extract-qt-installer.sh && \\\n")
        docker_file.write("    wget -nv https://download.qt.io/archive/qt/" + str(QT_MAJOR_VERISON) + "." + str(QT_MINOR_VERISON) + "/" + str(QT_MAJOR_VERISON) + "." + str(QT_MINOR_VERISON) + "." + str(QT_RELEASE_VERISON) + "/qt-opensource-linux-x64-" + str(QT_MAJOR_VERISON) + "." + str(QT_MINOR_VERISON) + "." + str(QT_RELEASE_VERISON) + ".run && \\\n")
        docker_file.write("    chmod +x qt-opensource-linux-x64-" + str(QT_MAJOR_VERISON) + "." + str(QT_MINOR_VERISON) + "." + str(QT_RELEASE_VERISON) + ".run && \\\n")
        docker_file.write("    QT_CI_PACKAGES=qt.qt5." + str(QT_MAJOR_VERISON) + str(QT_MINOR_VERISON) + str(QT_RELEASE_VERISON) + ".android \"$PWD\"/extract-qt-installer.sh \"$PWD\"/qt-opensource-linux-x64-" + str(QT_MAJOR_VERISON) + "." + str(QT_MINOR_VERISON) + "." + str(QT_RELEASE_VERISON) + ".run \"$QT_PATH\" && \\\n")
        docker_file.write("    rm qt-opensource-linux-x64-" + str(QT_MAJOR_VERISON) + "." + str(QT_MINOR_VERISON) + "." + str(QT_RELEASE_VERISON) + ".run && \\\n")
        docker_file.write("    rm extract-qt-installer.sh && \\\n")
        docker_file.write("    ${QT_PATH}/" + str(QT_MAJOR_VERISON) + "." + str(QT_MINOR_VERISON) + "." + str(QT_RELEASE_VERISON) + "/android/src/3rdparty/gradle/gradlew -v && \\\n")
        docker_file.write("    ${QT_PATH}/" + str(QT_MAJOR_VERISON) + "." + str(QT_MINOR_VERISON) + "." + str(QT_RELEASE_VERISON) + "/android/src/3rdparty/gradle/gradlew --dry-run --refresh-dependencies -b ${QT_PATH}/" + str(QT_MAJOR_VERISON) + "." + str(QT_MINOR_VERISON) + "." + str(QT_RELEASE_VERISON) + "/android/src/android/templates/build.gradle | exit 0\n")
        docker_file.write("\n")

        docker_file.write("RUN apt-get update && \\\n")
        docker_file.write("    apt-get install -y g++ ruby-dev && \\\n")
        docker_file.write("    rm -rf /var/lib/apt/lists/* && \\\n")
        docker_file.write("    gem install fastlane -NV\n")
        docker_file.write("\n")

        docker_file.close()

except Exception, e:
    print(str(e), file=sys.stderr)
    sys.exit(1)

sys.exit(0)
