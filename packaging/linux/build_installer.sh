#!/bin/bash
set -e

while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -t|--tag)
    TAG="$2"
    shift # past argument
    shift # past value
    ;;
    -l|--local)
    LOCAL=$(realpath "$2")
    shift # past argument
    shift # past value
    ;;
    -d|--build-dir)
    BUILD_DIR=$(realpath "$2")
    shift # past argument
    shift # past value
    ;;
    -r|--remote)
    REMOTE=YES
    shift # past argument
    ;;
    --nomatlab)
    NOMATLAB=YES
    shift # past argument
    ;;
    -h|--help)
    HELP=YES
    shift # past argument
    ;;
    *)    # unknown option
    echo >&2 "error: unrecognized command line option '$key'"
    shift
    ;;
esac
done

if [ -n "$HELP" ]; then
  echo "Usage: build_installer [options]"
  echo "Options:"
  echo "-h, --help		     Show this help message and exit"
  echo "-l <dir>, --local <dir>	     Clone RasCAL-2 from local directory (requires git)"
  echo "-d <dir>, --build-dir <dir>  Specify build directory (temp directory will be used if not provided)"
  echo "-t <arg>, --tag <arg>	     Clone specific tag of RasCAL-2 from local (requires git) or web"
  echo "-r, --remote		     Clone RasCAL-2 from Github repo"
  echo "--nomatlab		     Indicates that Matlab should not be added to installer"
  exit 0
fi


command -v makeself >/dev/null 2>&1 || {
  echo >&2 "makeself is required but not installed";
  exit 1;
}

# trap ctrl-c and call finish()
#trap finish INT EXIT

function finish() {
  [ -n "$TMP_DIR" ] && rm -rf "$TMP_DIR"
}

SRC_DIR=$(dirname "$(realpath "$0")")

echo ""
echo "RasCAL-2 Installer Builder"
echo ""

if [ -n "$BUILD_DIR" ]; then
  if [ "$(ls -A $BUILD_DIR)" ]; then
    echo >&2 "error: the build directory '$BUILD_DIR' must be empty"
    exit 1
  else
    TMP_DIR="$BUILD_DIR/build"
    mkdir "$TMP_DIR"
  fi
else
  TMP_DIR=$(mktemp -d)
fi

cd "$TMP_DIR"
mkdir "$TMP_DIR/rascal"

if [ -n "$REMOTE" ]; then
  echo "Downloading RasCAL-2 from remote repo"
  if [ -n "$TAG" ]; then
    RASCAL_URL="https://github.com/jeremyspencer39171/RasCAL-2/archive/${TAG}.tar.gz"
  else
    RASCAL_URL="https://github.com/jeremyspencer39171/RasCAL-2/tarball/main"
  fi

  wget $RASCAL_URL -O "$TMP_DIR/rascal.tar.gz"
  tar xzf "$TMP_DIR/rascal.tar.gz" -C "$TMP_DIR/rascal" --strip-components=1

elif [ -n "$LOCAL" ]; then
  command -v git >/dev/null 2>&1 || {
    echo >&2 "git is required with the --local option.";
    exit 1;
  }
  echo "Cloning RasCAL-2 from local directory"
  if [ -n "$TAG" ]; then
    git clone --branch "$TAG" "$LOCAL" "$TMP_DIR"/rascal
  else
    git clone "$LOCAL" "$TMP_DIR"/rascal
  fi
else
  echo >&2 "error: location of RasCAL-2 directory is not specified"
  echo "use --help option to see available commands"
  exit 1
fi


echo ""
echo "Downloading Miniconda"
echo ""
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O "$TMP_DIR/miniconda.sh"
bash ./miniconda.sh -b -p ./miniconda
./miniconda/bin/conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main --channel https://repo.anaconda.com/pkgs/r
./miniconda/bin/conda create -n rascal_builder -y python=3.10

echo ""
echo "Downloading Dependencies"
echo ""
python_exec="./miniconda/envs/rascal_builder/bin/python"
mkdir "$TMP_DIR/packages"
$python_exec -m pip download -r "./rascal/requirements.txt" --dest "$TMP_DIR/packages"

# workaround for matlab engine requires 2023a to installed on build machine
if [ -z "$NOMATLAB" ]; then
  $python_exec -m pip install matlabengine==9.14.*
fi

# workaround for centos 7
#$python_exec -m pip download --only-binary=":all:" --platform="manylinux_2_17_x86_64"  --dest "$TMP_DIR/packages" pillow==9.2

echo ""
echo "Compressing Package.tar.gz ..."
echo ""

STAGE_DIR="$TMP_DIR/stage"
mkdir "$STAGE_DIR"

mv -t "$STAGE_DIR" "rascal" "miniconda/envs" "packages"
chmod 777 "$STAGE_DIR/rascal/packaging/linux/install.sh"

echo ""
echo "Creating self-extracting archive"
echo ""
EXECUTABLE="RasCAL-2-installer.run"
if [ -n "$TAG" ]; then
  EXECUTABLE="RasCAL-2-${TAG:1}-installer.run"
fi

makeself --tar-format "posix" --tar-extra "--exclude=__pycache__ --exclude=.git --exclude=.github --exclude=rascal/doc --exclude=rascal/tests" "$STAGE_DIR" "$EXECUTABLE" "RasCAL-2 installer" ./rascal/packaging/linux/install.sh
cp -a "$EXECUTABLE" "$SRC_DIR/$EXECUTABLE"

exit 0
