import platform
import site

from PyInstaller.utils.hooks import collect_data_files

datas = collect_data_files(
    "ratapi",
    excludes=[
        "examples/**",
    ],
)

if platform.system() == "Linux":
    datas += [(site.getsitepackages()[0] + "/ratapi/eventManager.so", "ratapi")]
