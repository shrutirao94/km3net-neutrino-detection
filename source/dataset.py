import os
from path import Path
from source import utils
from torchvision import transforms
from torch.utils.data import Dataset, DataLoader

def default_transforms():
    """
    Initialise the transformations to apply to input pointclouds:
    1. Normalisation
    2. Random Rotation Around Z-Axiz
    3. Uniform Point Sampling
    4. Gaussian Sample Based Jitter

    Note: 8192 points are chosen to be uniformly sampled due to large point
    cloud sizes

    Parameters
    ----------
    parts: list of class Transform
        List of transforms to apply

    Returns
    -------
    Chained list of Transform classes

    """
    parts = [PointSampler(8192),
            Normalize(),
            RandRotation_z(),
            RandomNoise(),
            ToTensor()]

    return transforms.Compose(parts)


class PointCloudData(Dataset):
    """
    Obtains the class name and correspoinding point clouds, applys
    transformations and returns final tensor.

    Parameters
    ----------
    Dataset: Dataset Pytorch Object

    Returns
    -------
    pointcloud: tensor
        Transformed tensor
    """
    def __init__(self, root_dir, valid=False, folder="train", transform=default_transforms()):
        self.root_dir = root_dir
        folders = [dir for dir in sorted(os.listdir(root_dir)) if os.path.isdir(root_dir/dir)]
        self.classes = {folder: i for i, folder in enumerate(folders)}
        self.transforms = transform if not valid else default_transforms()
        self.valid = valid
        self.files = []

        for category in self.classes.keys():
            new_dir = root_dir/Path(category)/folder
            for file in os.listdir(new_dir):
                if file.endswith('.off'):
                    sample = {}
                    sample['pcd_path'] = new_dir/file
                    sample['category'] = category
                    self.files.append(sample)

    def __len__(self):
        return len(self.files)

    def __preproc__(self, file):
        verts, faces = read_off(file)

        if self.transforms:
            pointcloud = self.transforms((verts, faces))
        return pointcloud

    def __getitem__(self, idx):
        pcd_path = self.files[idx]['pcd_path']
        category = self.files[idx]['category']

        with open(pcd_path, 'r') as f:
            pointcloud = self.__preproc__(f)

        return {'pointcloud': pointcloud,
                'category': self.classes[category]}
