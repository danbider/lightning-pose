"""Path handling functions."""

from omegaconf import DictConfig, OmegaConf, ListConfig
import os
import pandas as pd
from typeguard import typechecked
from typing import Any, List, Tuple, Union, Optional


#@typechecked
def ckpt_path_from_base_path(
    base_path: str,
    model_name: str,
    logging_dir_name: str = "tb_logs/",
    version: int = 0,
) -> str:
    """Given a path to a hydra output with trained model, extract the model .ckpt file.

    Args:
        base_path (str): path to a folder with logs and checkpoint. for example,
            function will search base_path/logging_dir_name/model_name...
        model_name (str): the name you gave your model before training it; appears as
            model_name in lightning-pose/scripts/config/model_params.yaml
        logging_dir_name (str, optional): name of the folder in logs, controlled in
            train_hydra.py Defaults to "tb_logs/".
        version (int. optional):

    Returns:
        str: path to model checkpoint

    """
    # TODO: consider finding the most recent hydra path containing logging_dir_name
    import glob

    model_search_path = os.path.join(
        base_path,
        logging_dir_name,  # TODO: may change when we switch from Tensorboard
        model_name,  # get the name string of the model (determined pre-training)
        "version_%i" % version,  # always version_0 because ptl starts a version_0 dir
        "checkpoints",
        "*.ckpt",
    )
    # TODO: we're taking the last ckpt. make sure that with multiple checkpoints, this
    # is what we want
    model_ckpt_path = glob.glob(model_search_path)[-1]
    return model_ckpt_path


#@typechecked
def check_if_semi_supervised(
    losses_to_use: Union[ListConfig, list, None] = None
) -> bool:
    """Use config file to determine if model is semi-supervised.

    Take the entry of the hydra cfg that specifies losses_to_use. If it contains
    meaningful entries, infer that we want a semi_supervised model.

    Args:
        losses_to_use (Union[ListConfig, list, None], optional): the cfg entry
            specifying semisupervised losses to use. Defaults to None.

    Returns:
        bool: True if the model is semi_supervised. False otherwise.

    """
    if losses_to_use is None:  # null
        semi_supervised = False
    elif len(losses_to_use) == 0:  # empty list
        semi_supervised = False
    elif (
        len(losses_to_use) == 1 and losses_to_use[0] == ""
    ):  # list with an empty string
        semi_supervised = False
    else:
        semi_supervised = True
    return semi_supervised


#@typechecked
def load_label_csv_from_cfg(cfg: Union[DictConfig, dict]) -> pd.DataFrame:
    """Helper function for easy loading.

    Args:
        cfg: DictConfig

    Returns:
        pd.DataFrame
    """

    csv_file = os.path.join(cfg["data"]["data_dir"], cfg["data"]["csv_file"])
    labels_df = pd.read_csv(csv_file, header=list(cfg["data"]["header_rows"]), index_col=0)
    return labels_df


#@typechecked
def get_keypoint_names(
    cfg: Optional[DictConfig] = None,
    csv_file: Optional[str] = None,
    header_rows: Optional[list] = None,
) -> List[str]:
    if os.path.exists(csv_file):
        if header_rows is None:
            if "header_rows" in cfg.data:
                header_rows = list(cfg.data.header_rows)
            else:
                # assume dlc format
                header_rows = [0, 1, 2]
        csv_data = pd.read_csv(csv_file, header=header_rows)
        # collect marker names from multiindex header
        if header_rows == [1, 2] or header_rows == [0, 1]:
            # self.keypoint_names = csv_data.columns.levels[0]
            # ^this returns a sorted list for some reason, don't want that
            keypoint_names = [b[0] for b in csv_data.columns if b[1] == "x"]
        elif header_rows == [0, 1, 2]:
            # self.keypoint_names = csv_data.columns.levels[1]
            keypoint_names = [b[1] for b in csv_data.columns if b[2] == "x"]
    else:
        keypoint_names = ["bp_%i" % n for n in range(cfg.data.num_targets // 2)]
    return keypoint_names


# --------------------------------------------------------------------------------------
# Path handling functions for running toy dataset
# --------------------------------------------------------------------------------------


#@typechecked
def return_absolute_path(possibly_relative_path: str, n_dirs_back=3) -> str:
    """Return absolute path from possibly relative path."""
    if os.path.isabs(possibly_relative_path):
        # absolute path already; do nothing
        abs_path = possibly_relative_path
    else:
        # our toy_dataset in relative path
        cwd_split = os.getcwd().split(os.path.sep)
        desired_path_list = cwd_split[:-n_dirs_back]
        if desired_path_list[-1] == "multirun":
            # hydra multirun, go one dir back
            desired_path_list = desired_path_list[:-1]
        abs_path = os.path.join(os.path.sep, *desired_path_list, possibly_relative_path)
    if not os.path.exists(abs_path):
        raise IOError("%s is not a valid path" % abs_path)
    return abs_path


#@typechecked
def return_absolute_data_paths(data_cfg: DictConfig) -> Tuple[str, str]:
    """Generate absolute path for our example toy data.

    @hydra.main decorator switches the cwd when executing the decorated function, e.g.,
    our train(). so we're in some /outputs/YYYY-MM-DD/HH-MM-SS folder.

    Args:
        data_cfg (DictConfig): data config file with paths to data and video folders.

    Returns:
        Tuple[str, str]: absolute paths to data and video folders.

    """
    data_dir = return_absolute_path(data_cfg.data_dir)
    if os.path.isabs(data_cfg.video_dir):
        video_dir = data_cfg.video_dir
    else:
        video_dir = os.path.join(data_dir, data_cfg.video_dir)
    # assert that those paths exist and in the proper format
    assert os.path.isdir(data_dir)
    assert os.path.isdir(video_dir) or os.path.isfile(video_dir)
    return data_dir, video_dir

# def find_vids_in_dir(folder_path: str) -> List[str]:
#     # get all video files in directory
#     vid_files = [f for f in os.listdir(folder_path) if f.endswith((".mp4", ".avi", ".mov"))]
#     # get absolute paths of video files and check that they exist
#     absolute_paths = [os.path.join(folder_path, v) for v in vid_files if os.path.isfile(os.path.join(folder_path, v))]
#     return absolute_paths

#@typechecked
def get_videos_in_dir(video_dir: str, return_mp4_only: bool = True) -> List[str]:
    # gather videos to process
    # TODO: check if you're give a path to a single video?
    assert os.path.isdir(video_dir)
    # get all video files in directory, from allowed formats
    allowed_formats = (".mp4", ".avi", ".mov")
    if return_mp4_only == True:
        allowed_formats = ".mp4"
    video_files = [os.path.join(video_dir, f) for f in os.listdir(video_dir) if f.endswith(allowed_formats)]

    if len(video_files) == 0:
        raise IOError("Did not find any valid video files in %s" % video_dir)
    return video_files


#@typechecked
def check_video_paths(video_paths: Union[List[str], str]) -> list:
    # get input data
    if isinstance(video_paths, list):
        # presumably a list of files
        filenames = video_paths
    elif isinstance(video_paths, str) and os.path.isfile(video_paths):
        # single video file
        filenames = [video_paths]
    elif isinstance(video_paths, str) and os.path.isdir(video_paths):
        # directory of videos
        filenames = get_videos_in_dir(video_paths)
    else:
        raise ValueError(
            "`video_paths_list` must be a list of files, a single file, "
            + "or a directory name"
        )
    for filename in filenames:
        assert filename.endswith(".mp4"), "video files must be mp4 format!"

    return filenames


# --------------------------------------------------------------------------------------
# Path handling for predictions on new videos
# --------------------------------------------------------------------------------------


#@typechecked
class VideoPredPathHandler:
    """class that defines filename for a predictions .csv file, given video file and
    model specs.
    """

    def __init__(
        self, save_preds_dir: str, video_file: str, model_cfg: DictConfig
    ) -> None:
        self.video_file = video_file
        self.save_preds_dir = save_preds_dir
        self.model_cfg = model_cfg
        self.check_input_paths()

    @property
    def video_basename(self) -> str:
        return os.path.basename(self.video_file).split(".")[0]

    @property
    def loss_str(self) -> str:
        semi_supervised = check_if_semi_supervised(self.model_cfg.model.losses_to_use)
        loss_names = []
        loss_weights = []
        loss_str = ""
        if semi_supervised:  # add the loss names and weights
            loss_str = ""
            if len(self.model_cfg.model.losses_to_use) > 0:
                loss_names = list(self.model_cfg.model.losses_to_use)
                for loss in loss_names:
                    loss_weights.append(self.model_cfg.losses[loss]["log_weight"])

                loss_str = ""
                for loss, weight in zip(loss_names, loss_weights):
                    loss_str += "_" + loss + "_" + str(weight)

            else:  # fully supervised, return empty string
                loss_str = ""
        return loss_str

    def check_input_paths(self) -> None:
        assert os.path.isfile(self.video_file)
        assert os.path.isdir(self.save_preds_dir)

    def build_pred_file_basename(self, extra_str="") -> str:
        return "%s_%s%s%s.csv" % (
            self.video_basename,
            self.model_cfg.model.model_type,
            self.loss_str,
            extra_str,
        )

    def __call__(self, extra_str="") -> str:
        pred_file_basename = self.build_pred_file_basename(extra_str=extra_str)
        return os.path.join(self.save_preds_dir, pred_file_basename)
