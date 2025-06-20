import pathlib
import shutil
import sys

import PyInstaller.__main__ as pyi

FILE_PATH = pathlib.Path(__file__).resolve()
PACKAGING_PATH = FILE_PATH.parent
PROJECT_PATH = PACKAGING_PATH.parent

EXCLUDED_IMPORT = [
    "jedi",
    "tkinter",
    "IPython",
    "lib2to3",
    "PyQt6.QtDBus",
    "PyQt6.QtDesigner",
    "PyQt6.QtBluetooth",
    "PyQt6.QtNetwork",
    "PyQt6.QtNfc",
    "PyQt6.QtWebChannel",
    "PyQt6.QtWebEngine",
    "PyQt6.QtWebEngineCore",
    "PyQt6.QtWebEngineWidgets",
    "PyQt6.QtWebKit",
    "PyQt6.QtWebKitWidgets",
    "PyQt6.QtWebSockets",
    "PyQt6.QtTest",
    "PyQt6.QtTextToSpeech",
    "PyQt6.QtWinExtras",
    "PyQt6.QtLocation",
    "PyQt6.QtMultimediaWidgets",
    "PyQt6.QtNetworkAuth",
    "PyQt6.QtPositioning",
    "PyQt6.QtQuick",
    "PyQt6.QtQuick3D",
    "PyQt6.QtSensors",
    "PyQt6.QtRemoteObjects",
    "PyQt6.QtMultimedia",
    "PyQt6.QtQml",
    "PyQt6.QtQuickWidgets",
    "PyQt6.QtSql",
    "PyQt6.QtSvg",
    "PyQt6.QtSerialPort",
    "PyQt6.QtNetwork",
    "PyQt6.QtScript",
    "PyQt6.QtXml",
    "PyQt6.QtXmlPatterns",
    "sphinx",
    "numpy.array_api",
    "pkg_resources",
]
IS_WINDOWS = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"


def build_exe():
    """Builds the executable for the rascal-2 application"""
    work_path = PACKAGING_PATH / "temp"
    dist_path = PACKAGING_PATH / "bundle"
    main_path = PROJECT_PATH / "rascal2" / "main.py"
    shutil.rmtree(dist_path, ignore_errors=True)

    pyi_args = [
        "--name",
        "rascal",
        "--specpath",
        str(work_path),
        "--workpath",
        str(work_path),
        "--windowed",
        "--noconfirm",
        "--distpath",
        str(dist_path),
        "--clean",
        "--additional-hooks-dir",
        str(PACKAGING_PATH / "hooks"),
        "--log-level",
        "ERROR",
        str(main_path),
    ]

    for exclude in EXCLUDED_IMPORT:
        pyi_args.extend(["--exclude-module", exclude])

    if IS_WINDOWS:
        pyi_args.extend(["--icon", str(PACKAGING_PATH / "icons" / "logo.ico")])
    if IS_MAC:
        pyi_args.extend(["--icon", str(PACKAGING_PATH / "icons" / "logo.icns")])

    print("Building RasCAL-2 with PyInstaller")
    pyi.run(pyi_args)

    exec_folder = next(dist_path.iterdir())
    if not IS_MAC:
        exec_folder.rename(dist_path / "bin")
    shutil.rmtree(work_path)

    # Copy resources into installer directory
    resources = ["static/images", "static/style.css"]
    shutil.copy(PROJECT_PATH / "LICENSE", dist_path / "LICENSE")
    for resource in resources:
        if IS_MAC:
            dest_path = dist_path / "rascal.app" / "Contents" / "Resources" / resource
        else:
            dest_path = dist_path / resource
        src_path = PROJECT_PATH / "rascal2" / resource
        if src_path.is_file():
            shutil.copy(src_path, dest_path)
        else:
            shutil.copytree(src_path, dest_path, ignore=shutil.ignore_patterns("__pycache__"))

    if IS_MAC:
        shutil.rmtree(PACKAGING_PATH / "bundle" / "app" / "rascal")

    print("RasCAL-2 built with no errors!\n")


if __name__ == "__main__":
    build_exe()
