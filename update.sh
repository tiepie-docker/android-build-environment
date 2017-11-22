#!/bin/bash -e

# A POSIX variable
OPTIND=1 # Reset in case getopts has been used previously in the shell.

while getopts "a:v:q:u:d:s:i:o:n:" opt; do
    case "$opt" in
    a)  ARCH=$OPTARG
        ;;
    v)  VERSION=$OPTARG
        ;;
    q)  QEMU_ARCH=$OPTARG
        ;;
    u)  QEMU_VER=$OPTARG
        ;;
    d)  DOCKER_REPO=$OPTARG
        ;;
    s)  SUITE=$OPTARG
        ;;
    i)  INCLUDE=$OPTARG
        ;;
    o)  UNAME_ARCH=$OPTARG
        ;;
    n)  NDK_VERSION=$OPTARG
        ;;
    esac
done

shift $((OPTIND-1))

[ "$1" = "--" ] && shift

INCLUDE_FILES=(packages/all.txt packages/${SUITE}-all.txt packages/all-${ARCH}.txt packages/${SUITE}-${ARCH}.txt)
for include_file in ${INCLUDE_FILES[@]}; do
    if [ -s ${include_file} ]; then
        INCLUDE+=,$(sed ':a;N;$!ba;s/\n/,/g' ${include_file})
    fi
done

dir="$VERSION"
COMPONENTS="main,universe"
VARIANT="minbase"
args=( -d "$dir" debootstrap --variant="$VARIANT" --components="$COMPONENTS" --include="$INCLUDE" --arch="$ARCH" "$SUITE" )

mkdir -p mkimage $dir
curl https://raw.githubusercontent.com/docker/docker/master/contrib/mkimage.sh > mkimage.sh
curl https://raw.githubusercontent.com/docker/docker/master/contrib/mkimage/debootstrap > mkimage/debootstrap
chmod +x mkimage.sh mkimage/debootstrap
patch -f mkimage.sh < patch/mkimage.patch
if [ "$?" != 0 ]; then exit 1; fi

mkimage="$(readlink -f "${MKIMAGE:-"mkimage.sh"}")"
{
    echo "$(basename "$mkimage") ${args[*]/"$dir"/.}"
    echo
    echo 'https://github.com/docker/docker/blob/master/contrib/mkimage.sh'
} > "$dir/build-command.txt"

sudo DEBOOTSTRAP="qemu-debootstrap" nice ionice -c 3 "$mkimage" "${args[@]}" 2>&1 | tee "$dir/build.log"
cat "$dir/build.log"
sudo chown -R "$(id -u):$(id -g)" "$dir"

xz -d < $dir/rootfs.tar.xz | gzip -c > $dir/rootfs.tar.gz
sed -i /^ENV/d "${dir}/Dockerfile"
cat >> "${dir}/Dockerfile" <<EOF
ENV ARCH=${UNAME_ARCH} UBUNTU_SUITE=${SUITE} DOCKER_REPO=${DOCKER_REPO}
ENV ANDROID_NDK_PATH=/opt/android-ndk-${NDK_VERSION} ANDROID_SDK_PATH=/opt/android-sdk
ENV ANDROID_NDK_ROOT=\${ANDROID_NDK_PATH} ANDROID_SDK_ROOT=\${ANDROID_SDK_PATH}
ENV QT_PATH=/opt/Qt

RUN wget -nv https://dl.google.com/android/repository/android-ndk-${NDK_VERSION}-linux-x86_64.zip && \
    unzip -q android-ndk-${NDK_VERSION}-linux-x86_64.zip -d /opt && \
    rm android-ndk-${NDK_VERSION}-linux-x86_64.zip

RUN apt-get update && \
    apt-get install -y openjdk-8-jdk && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN wget -nv https://dl.google.com/android/repository/sdk-tools-linux-3859397.zip && \
    mkdir -p /opt/android-sdk && \
    unzip -q sdk-tools-linux-3859397.zip -d /opt/android-sdk && \
    rm sdk-tools-linux-3859397.zip && \
    cd /opt/android-sdk/tools/bin && \
    yes | ./sdkmanager --licenses && \
    ./sdkmanager "tools" "platform-tools" "platforms;android-23" "build-tools;23.0.3"

RUN curl https://raw.githubusercontent.com/benlau/qtci/master/bin/extract-qt-installer > extract-qt-installer.sh && \
    chmod +x extract-qt-installer.sh && \
    wget -nv https://download.qt.io/archive/qt/5.9/5.9.2/qt-opensource-linux-x64-5.9.2.run && \
    chmod +x qt-opensource-linux-x64-5.9.2.run && \
    QT_CI_PACKAGES=qt.592.android_x86,qt.592.android_armv7 "\$PWD"/extract-qt-installer.sh "\$PWD"/qt-opensource-linux-x64-5.9.2.run "\$QT_PATH" && \
    rm qt-opensource-linux-x64-5.9.2.run && \
    rm extract-qt-installer.sh
EOF

if [ "$DOCKER_REPO" ]; then
    docker build -t "${DOCKER_REPO}:${ARCH}-${SUITE}-slim" "${dir}"
    mkdir -p "${dir}/full"
    (
    cd "${dir}/full"
    if [ ! -f x86_64_qemu-${QEMU_ARCH}-static.tar.gz ]; then
        wget -N https://github.com/multiarch/qemu-user-static/releases/download/${QEMU_VER}/x86_64_qemu-${QEMU_ARCH}-static.tar.gz
    fi
    tar xf x86_64_qemu-*.gz
    )
    cat > "${dir}/full/Dockerfile" <<EOF
FROM ${DOCKER_REPO}:${ARCH}-${SUITE}-slim
ADD qemu-*-static /usr/bin/
EOF
    docker build -t "${DOCKER_REPO}:${ARCH}-${SUITE}" "${dir}/full"
fi

docker run -it --rm "${DOCKER_REPO}:${ARCH}-${SUITE}" bash -xc '
    uname -a
    echo
    cat /etc/apt/sources.list
    echo
    cat /etc/os-release 2>/dev/null
    echo
    cat /etc/lsb-release 2>/dev/null
    echo
    cat /etc/debian_version 2>/dev/null
    true
'