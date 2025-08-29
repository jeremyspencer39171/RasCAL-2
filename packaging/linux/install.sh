#!/bin/bash
set -e

function on_error_log_and_exit() {
  if (( $? )) ; then
    cat $tmp_log
    rm $tmp_log
    exit 1
  fi
}


echo ""
echo "Welcome to the RasCAL-2 Installer"
echo ""

INSTALL_EDITOR="n"

# Create destination folder
if [[ $EUID -ne 0 ]]; then
    INSTALL_DIR="$HOME/RasCAL-2"
    MENU_DIR="$HOME/.local/share/applications"
    MENU_PATH="$MENU_DIR/RasCAL-2.desktop"
    LINK_DIR="$HOME/.local/bin/"
    LINK_PATH="$LINK_DIR/rascal"
    USER=$(whoami)
else
    INSTALL_DIR="/usr/local/RasCAL-2"
    MENU_DIR="/usr/share/applications"
    MENU_PATH="$MENU_DIR/RasCAL-2.desktop"
    LINK_DIR="/usr/local/bin/"
    LINK_PATH="$LINK_DIR/rascal"
    USER=$SUDO_USER
    if [[ "$USER" == "" ]]; then
      USER=$LOGNAME
    fi
fi

ACCEPT=0
PASSED_INSTALL_DIR=0
INSTALL_EXAMPLES="?"

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --accept) ACCEPT=1 ;;
        --install-dir) INSTALL_DIR="$2"; PASSED_INSTALL_DIR=1; shift ;;
        --install-examples) INSTALL_EXAMPLES="y" ;;
        --matlab) MATLAB_PATH="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done


if [[ $ACCEPT != 1 ]]; then
  # Show License
  more < "./rascal/LICENSE"

  while true
  do
    echo ""
    echo "Do you accept all of the terms of the preceding license agreement? (y/n):"
    read -r REPLY
    REPLY=$(echo "$REPLY" | tr '[:upper:]' '[:lower:]')
    if [[ "$REPLY" != y && "$REPLY" != n ]]; then
        echo "        <Please answer y for yes or n for no>" > /dev/tty
    fi
  
    if [ "$REPLY" == y ]; then
        break
    fi
  
    if [ "$REPLY" == n ]; then
        echo "Aborting installation"
        exit 1
    fi
  done
fi

if [[ $PASSED_INSTALL_DIR != 1 ]]; then
  echo ""
  echo "Please enter the directory to install in
  (The default is \"$INSTALL_DIR\")"
  read -r DIR_NAME

  if [ "$DIR_NAME" != "" ]; then
      INSTALL_DIR=$DIR_NAME
  fi
fi

if [[ -d "$INSTALL_DIR" && "$(ls -A "$INSTALL_DIR")" != "" ]]; then
while true
do
    echo ""
    echo "The destination folder ($INSTALL_DIR) exists. Do you want to remove it? (y/n)"
    read -r REPLY
    REPLY=$(echo "$REPLY" | tr '[:upper:]' '[:lower:]')
    if [ "$REPLY" != y ] && [ "$REPLY" != n ]; then
        echo "        <Please answer y for yes or n for no>" > /dev/tty
    fi
    if [ "$REPLY" = y ]; then
        echo "Removing old installation"

	if ! rm -rf "$INSTALL_DIR"; then
	    echo "Failed to remove old installation"
	    echo "Aborting installation"
	    exit 1
	fi
	break
    fi
    if [ "$REPLY" = n ]; then
	echo "Aborting installation"
	exit 0
    fi
done
fi

if [ ! -d  "$INSTALL_DIR" ]; then
    if ! mkdir -p "$INSTALL_DIR"; then
         echo "The $INSTALL_DIR directory does not exist and could not be created."
    exit 1
  fi
fi

if [[ $INSTALL_EXAMPLES != "y" ]]; then
  echo ""
  echo "Install example projects? (y/n) [$INSTALL_EXAMPLES]: "
  read -r INSTALL_FLAG
  if [ "$INSTALL_FLAG" != "" ]; then
      INSTALL_EXAMPLES=$INSTALL_FLAG
  else
      INSTALL_EXAMPLES="y"
  fi
fi

echo ""
echo "Building executable (This should take a few minutes) ..."

EXIT_CODE=0
tmp_log=$(mktemp)

python_exec="./envs/rascal_builder/bin/python"
CFLAGS=$(./envs/rascal_builder/bin/python3-config --includes)
export CFLAGS=$CFLAGS
($python_exec -m pip install --no-cache-dir --no-index --find-links packages -r "./rascal/requirements.txt" --target "./envs/rascal_builder/lib/python3.10/site-packages" || EXIT_CODE=$?) &>$tmp_log
on_error_log_and_exit
($python_exec "./rascal/packaging/build_exe.py" || EXIT_CODE=$?) &>$tmp_log
on_error_log_and_exit

echo ""
echo "Copying executable and other files ..."

GROUP=$(id -gn "$USER")
cp -ar "./rascal/packaging/bundle/." "${INSTALL_DIR}"
if [ "$INSTALL_EXAMPLES" = y ]; then
    cp -ar "./rascal/examples" "$INSTALL_DIR/examples"
fi
chown -R "$USER:$GROUP" "$INSTALL_DIR"


ARCH_FILE="$INSTALL_DIR/bin/_internal/matlab/engine/_arch.txt"
if [ -f "$ARCH_FILE" ]; then
  if [ -z ${MATLAB_PATH+x} ]; then
    echo ""
    echo "Specify MATLAB directory (Optional) i.e. \"/usr/local/MATLAB/R2023a\"
(Min supported version is R2023a, leave empty to skip MATLAB setup)"
    read -r MATLAB_PATH
  fi
  if [ "$MATLAB_PATH" != "" ]; then
      MATLAB_INSTALL_PATH=$MATLAB_PATH/bin/glnxa64
      MATLAB_ENGINE_PATH=$MATLAB_PATH/extern/engines/python/dist/matlab/engine/glnxa64
      MATLAB_BIN_PATH=$MATLAB_PATH/extern/bin/glnxa64
      if ! [[ -d $MATLAB_INSTALL_PATH && -d $MATLAB_ENGINE_PATH && -d $MATLAB_BIN_PATH ]]; then
    	  echo "One or more paths required for MATLAB setup were not found. Please confirm these exist then run setup in the RasCAL software: "
    	  echo "--> $MATLAB_INSTALL_PATH"
    	  echo "--> $MATLAB_ENGINE_PATH"
    	  echo "--> $MATLAB_BIN_PATH"
      	  MATLAB_PATH=""
      fi
  fi

  if [[ $EUID -ne 1 ]]; then
     chmod 664 $ARCH_FILE
  fi

  # Update arch file if MATLAB path is given
  if [ "$MATLAB_PATH" != "" ]; then
     printf "glnxa64\n$MATLAB_INSTALL_PATH\n$MATLAB_ENGINE_PATH\n$MATLAB_BIN_PATH" > $ARCH_FILE
  fi
fi

# Create Desktop Entry for RasCAL-2
if [ ! -d "$MENU_DIR" ]; then
    echo "Creating $MENU_DIR"
    mkdir $MENU_DIR
fi

DESKTOP_ENTRY="[Desktop Entry]
Name=RasCAL-2
Comment=GUI for Reflectivity Algorithm Toolbox (RAT)
Exec=$INSTALL_DIR/bin/rascal
Icon=$INSTALL_DIR/static/images/logo.png
Type=Application
StartupNotify=true"

if ! echo "$DESKTOP_ENTRY" > $MENU_PATH; then
    echo "Failed to create menu entry for RasCAL-2"
else
    chmod 644 "$MENU_DIR/RasCAL-2.desktop"
fi

# Create global link
if [ ! -d $LINK_DIR ]; then
    mkdir $LINK_DIR
fi

ln -sf  "$INSTALL_DIR/bin/rascal" ${LINK_PATH}

echo ""
echo "Installation complete."
echo ""

# Exit from the script with success (0)
rm $tmp_log
exit 0
