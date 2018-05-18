from __future__ import print_function
import os
import sys
import json
from subprocess import check_call
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument('--suite', required=True)
parser.add_argument('--docker-repo', required=True)
parser.add_argument('--ndk-version', required=True)
parser.add_argument('--qt-major-version', type=int, required=True)
parser.add_argument('--qt-minor-version', type=int, required=True)
parser.add_argument('--qt-release-version', type=int, required=True)

args = parser.parse_args()

try:
    build_directory = "build"

    if not os.path.exists(build_directory):
        os.mkdir(build_directory)

    # Download image:
    image_file_name = "ubuntu-" + args.suite + "-core-cloudimg-amd64-root.tar.gz"
    if not os.path.exists(build_directory + "/" + image_file_name):
        print("Download image file")
        base_url = "https://partner-images.canonical.com/core"
        try:
            check_call(["wget", "-O", build_directory + "/" + image_file_name, base_url + "/" + args.suite + "/current/" + image_file_name])
        except Exception, e:
            print("Failed to download file trying unsupported directory", file=sys.stderr)
            check_call(["wget", "-O", build_directory + "/" + image_file_name, base_url + "/unsupported/" + args.suite + "/current/" + image_file_name])

    # Read packages.json:
    packages = []
    with open("packages.json") as f:
        data = json.load(f)
        if "all" in data:
            packages += data["all"]
        if args.suite in data:
            packages += data[args.suite]
        packages = list(set(packages))

    # Create Docker file:
    docker_file = open("build/Dockerfile", "w")
    docker_file.write("FROM scratch\n")
    docker_file.write("\n")

    docker_file.write("ADD " + image_file_name + " /\n")
    docker_file.write("\n")

    docker_file.write("ENV DEBIAN_FRONTEND=noninteractive\n")
    docker_file.write("ENV DEBCONF_NONINTERACTIVE_SEEN=true\n")
    docker_file.write("\n")

    docker_file.write("RUN set -xe && \\\n")
    docker_file.write("    echo '#!/bin/sh' > /usr/sbin/policy-rc.d && \\\n")
    docker_file.write("    echo 'exit 101' >> /usr/sbin/policy-rc.d && \\\n")
    docker_file.write("    chmod +x /usr/sbin/policy-rc.d && \\\n")
    docker_file.write("    dpkg-divert --local --rename --add /sbin/initctl && \\\n")
    docker_file.write("    cp -a /usr/sbin/policy-rc.d /sbin/initctl && \\\n")
    docker_file.write("    sed -i 's/^exit.*/exit 0/' /sbin/initctl && \\\n")
    docker_file.write("    echo 'force-unsafe-io' > /etc/dpkg/dpkg.cfg.d/docker-apt-speedup && \\\n")
    docker_file.write("    echo 'DPkg::Post-Invoke { \"rm -f /var/cache/apt/archives/*.deb /var/cache/apt/archives/partial/*.deb /var/cache/apt/*.bin || true\"; };' > /etc/apt/apt.conf.d/docker-clean && \\\n")
    docker_file.write("    echo 'APT::Update::Post-Invoke { \"rm -f /var/cache/apt/archives/*.deb /var/cache/apt/archives/partial/*.deb /var/cache/apt/*.bin || true\"; };' >> /etc/apt/apt.conf.d/docker-clean && \\\n")
    docker_file.write("    echo 'Dir::Cache::pkgcache \"\"; Dir::Cache::srcpkgcache \"\";' >> /etc/apt/apt.conf.d/docker-clean && \\\n")
    docker_file.write("    echo 'Acquire::Languages \"none\";' > /etc/apt/apt.conf.d/docker-no-languages && \\\n")
    docker_file.write("    echo 'Acquire::GzipIndexes \"true\"; Acquire::CompressionTypes::Order:: \"gz\";' > /etc/apt/apt.conf.d/docker-gzip-indexes && \\\n")
    docker_file.write("    echo 'Apt::AutoRemove::SuggestsImportant \"false\";' > /etc/apt/apt.conf.d/docker-autoremove-suggests && \\\n")
    docker_file.write("    apt-get clean && \\\n")
    docker_file.write("    rm -rf /var/lib/apt/lists/*\n")
    docker_file.write("\n")

    docker_file.write("RUN apt-get update && \\\n")
    docker_file.write("    apt-get dist-upgrade -y && \\\n")
    docker_file.write("    apt-get install -y apt-utils && \\\n")
    docker_file.write("    apt-get clean && \\\n")
    docker_file.write("    rm -rf /var/lib/apt/lists/*\n")

    if packages:
        docker_file.write("RUN apt-get update && \\\n")
        docker_file.write("    apt-get install -y " + (" \\\n" + " " * 23).join(packages) + " && \\\n")
        docker_file.write("    apt-get clean && \\\n")
        docker_file.write("    rm -rf /var/lib/apt/lists/*\n")
        docker_file.write("\n")

    if args.suite == "xenial":
        docker_file.write("RUN wget -nv --content-disposition https://packagecloud.io/github/git-lfs/packages/ubuntu/xenial/git-lfs_2.3.4_amd64.deb/download.deb && \\\n")
        docker_file.write("    dpkg -i git-lfs_2.3.4_amd64.deb && \\\n")
        docker_file.write("    rm git-lfs_2.3.4_amd64.deb\n")
        docker_file.write("\n")

    docker_file.write("ENV ANDROID_NDK_PATH=/opt/android-ndk-" + args.ndk_version + "\n")
    docker_file.write("ENV ANDROID_NDK_ROOT=/opt/android-ndk-" + args.ndk_version + "\n")
    docker_file.write("ENV ANDROID_SDK_PATH=/opt/android-sdk\n")
    docker_file.write("ENV ANDROID_SDK_ROOT=/opt/android-sdk\n")
    docker_file.write("ENV QT_PATH=/opt/Qt\n")
    docker_file.write("ENV QT_VERSION=" + str(args.qt_major_version) + "." + str(args.qt_minor_version) + "." + str(args.qt_release_version) + "\n")
    docker_file.write("\n")

    docker_file.write("RUN wget -nv https://dl.google.com/android/repository/android-ndk-" + args.ndk_version + "-linux-x86_64.zip && \\\n")
    docker_file.write("    unzip -q android-ndk-" + args.ndk_version + "-linux-x86_64.zip -d /opt && \\\n")
    docker_file.write("    rm /android-ndk-" + args.ndk_version + "-linux-x86_64.zip \n")
    docker_file.write("\n")

    docker_file.write("RUN wget -nv https://dl.google.com/android/repository/sdk-tools-linux-3859397.zip && \\\n")
    docker_file.write("    mkdir -p /opt/android-sdk && \\\n")
    docker_file.write("    unzip -q sdk-tools-linux-3859397.zip -d /opt/android-sdk && \\\n")
    docker_file.write("    rm sdk-tools-linux-3859397.zip && \\\n")
    docker_file.write("    cd /opt/android-sdk/tools/bin && \\\n")
    docker_file.write("    yes | ./sdkmanager --licenses && \\\n")
    docker_file.write("    ./sdkmanager \"tools\" \"platform-tools\" \"platforms;android-23\" \"build-tools;23.0.3\"\n")
    docker_file.write("\n")

    docker_file.write("RUN curl https://raw.githubusercontent.com/benlau/qtci/master/bin/extract-qt-installer > extract-qt-installer.sh && \\\n")
    docker_file.write("    chmod +x extract-qt-installer.sh && \\\n")
    docker_file.write("    wget -nv https://download.qt.io/archive/qt/" + str(args.qt_major_version) + "." + str(args.qt_minor_version) + "/" + str(args.qt_major_version) + "." + str(args.qt_minor_version) + "." + str(args.qt_release_version) + "/qt-opensource-linux-x64-" + str(args.qt_major_version) + "." + str(args.qt_minor_version) + "." + str(args.qt_release_version) + ".run && \\\n")
    docker_file.write("    chmod +x qt-opensource-linux-x64-" + str(args.qt_major_version) + "." + str(args.qt_minor_version) + "." + str(args.qt_release_version) + ".run && \\\n")
    docker_file.write("    QT_CI_PACKAGES=qt." + str(args.qt_major_version) + str(args.qt_minor_version) + str(args.qt_release_version) + ".android_x86,qt." + str(args.qt_major_version) + str(args.qt_minor_version) + str(args.qt_release_version) + ".android_armv7 \"$PWD\"/extract-qt-installer.sh \"$PWD\"/qt-opensource-linux-x64-" + str(args.qt_major_version) + "." + str(args.qt_minor_version) + "." + str(args.qt_release_version) + ".run \"$QT_PATH\" && \\\n")
    docker_file.write("    rm qt-opensource-linux-x64-" + str(args.qt_major_version) + "." + str(args.qt_minor_version) + "." + str(args.qt_release_version) + ".run && \\\n")
    docker_file.write("    rm extract-qt-installer.sh && \\\n")
    docker_file.write("    ${QT_PATH}/" + str(args.qt_major_version) + "." + str(args.qt_minor_version) + "." + str(args.qt_release_version) + "/android_armv7/src/3rdparty/gradle/gradlew -v && \\\n")
    docker_file.write("    ${QT_PATH}/" + str(args.qt_major_version) + "." + str(args.qt_minor_version) + "." + str(args.qt_release_version) + "/android_armv7/src/3rdparty/gradle/gradlew --dry-run --refresh-dependencies -b ${QT_PATH}/" + str(args.qt_major_version) + "." + str(args.qt_minor_version) + "." + str(args.qt_release_version) + "/android_armv7/src/android/templates/build.gradle | exit 0\n")
    docker_file.write("\n")

    docker_file.write("CMD [\"/bin/bash\"]\n")
    docker_file.write("\n")

    docker_file.close()

    # Build Docker image:
    check_call(["sudo", "docker", "build", "-t", args.docker_repo + ":amd64-" + args.suite, "build"])

except Exception, e:
    print(str(e), file=sys.stderr)
    sys.exit(1)

sys.exit(0)
