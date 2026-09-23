from ayon_core.addon import AYONAddon, ITrayAction, IHostAddon, IPluginPaths

from .version import __version__
from .constants import COLMAP_ROOT_FOLDER

class COLMAPAddon(AYONAddon, IHostAddon, ITrayAction, IPluginPaths):
    label = "COLMAP"
    name = "colmap"
    version = __version__
    host_name = "colmap"

    def tray_init(self):
        return

    def on_action_trigger(self):
        from qtpy import QtWidgets

        QtWidgets.QMessageBox.information(None, "Hello", "Hello")

    def get_load_plugin_paths(self, host_name):
        return [str(COLMAP_ROOT_FOLDER / "plugins" / "load")]
