#!/bin/bash
PACKAGE_SOURCE_PATH=$1 # Path to the package source dir

echo "Manually applying patches to ${PACKAGE_SOURCE_PATH}"

# Apply CMakeLists_txt.patch
patch -p1 -d "${PACKAGE_SOURCE_PATH}" < "${PWD}/patches/sdl2_mixer-CMakeLists_txt.patch"
if [ $? -ne 0 ]; then
    echo "Error applying sdl2_mixer-CMakeLists_txt.patch"
    exit 1
fi

# Apply PrivateSdlFunctions_cmake.patch
patch -p1 -d "${PACKAGE_SOURCE_PATH}" < "${PWD}/patches/sdl2_mixer-PrivateSdlFunctions_cmake.patch"
if [ $? -ne 0 ]; then
    echo "Error applying sdl2_mixer-PrivateSdlFunctions_cmake.patch"
    exit 1
fi
echo "All patches applied successfully."