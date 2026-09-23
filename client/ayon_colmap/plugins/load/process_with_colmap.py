import re

from itertools import count
from pathlib import Path
from subprocess import check_call

from ayon_api import get_tasks

from ayon_core.lib.transcoding import IMAGE_EXTENSIONS
from ayon_core.pipeline import Anatomy
from ayon_core.pipeline.load import LoaderPlugin
from ayon_core.pipeline.template_data import get_template_data

class ProcessWithCOLMAP(LoaderPlugin):
    """Process with COLMAP loader plugin."""

    product_base_types = {"*"}
    product_types = product_base_types
    representations = {"*"}
    extensions = {
        ext.lstrip(".")
        for ext in IMAGE_EXTENSIONS
    }

    label = "Process with COLMAP"
    icon = "fa5s.images"
    color = "#cccccc"

    def load(self, context, name, namespace, options):
        task_name = "PHOTOGRAMMETRY"
        task_entity_dicts = tuple(get_tasks(
            context["project"]["name"],
            task_names=[task_name],
            task_types=["Photogrammetry"],
            folder_ids=[context["folder"]["id"]],
        ))

        if not task_entity_dicts:
            raise ValueError(
                f"No Task exists called {task_name} under folder {context['folder']['name']}"
            )

        if len(task_entity_dicts) > 1:
            raise ValueError(
                f"More than one Task exists called {task_name} under folder {context['folder']['name']}: {task_entity_dicts}"
            )

        template_data = get_template_data(context["project"], context["folder"], task_entity_dicts[0], "colmap")
        template_data["ext"] = "colmap"

        for version in count(1):
            template_data["version"] = version
            default_format = (
                Anatomy(
                    context["project"]["name"]
                ).templates_obj["work"].format(
                    template_data
                )
            )["default"]
            colmap_folder_path = Path(default_format["directory"]) / default_format["file"]
            if not colmap_folder_path.exists():
                break

        images_folder_path = colmap_folder_path / "images"
        images_folder_path.mkdir(parents=True)
        database_path = colmap_folder_path / "database.db"
        log_folder_path = colmap_folder_path / "logs"
        log_folder_path.mkdir(parents=True)

        representation_first_file_path = Path(self.filepath_from_context(context))
        for representation_file_path in (
            representation_first_file_path.parent.glob(
                re.sub(r"\d+(?=\.[^.]*$)", "*", representation_first_file_path.name)
            )
        ):
            (images_folder_path / representation_file_path.name).symlink_to(representation_file_path)

        check_call("colmap feature_extractor --database_path {} --image_path {} 2> {}".format(database_path, images_folder_path, log_folder_path / "feature_extractor.log"), shell=True)
        check_call("colmap exhaustive_matcher --database_path {} 2> {}".format(database_path, log_folder_path / "exhaustive_matcher.log"), shell=True)
        sparse_folder_path = colmap_folder_path / "sparse"
        sparse_folder_path.mkdir(parents=True)
        check_call("colmap mapper --database_path {} --image_path {} --output_path {} 2> {}".format(database_path, images_folder_path, sparse_folder_path, log_folder_path / "mapper.log"), shell=True)
