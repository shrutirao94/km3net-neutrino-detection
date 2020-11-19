def read_off(file):
    """
    Reads the .off files into vertices and faces

    Parameters
    ----------
    file: .off

    Returns
    -------
    verts: array (Float)
        Array of vertices obtained from the 3D mesh
    faces: array (Float)
        Array of triangular faces representing the surfaces in 3D mesh
    """
    if 'OFF' != file.readline().strip():
        raise('Not a valid OFF header')

    n_verts, n_faces, __ = tuple([int(s) for s in file.readline().strip().split(' ')])
    verts = [[float(s) for s in file.readline().strip().split(' ')] for i_vert in range(n_verts)]
    faces = [[int(s) for s in file.readline().strip().split(' ')][1:] for i_face in range(n_faces)]

    return verts, faces


class PointSampler(object):
    def __init__(self, output_size):
        assert isinstance(output_size, int)
        self.output_size = output_size


    def triangle_area(self, pt1, pt2, pt3):
        """
        Calculates the area of triangular face

        Parameters
        ----------
        pt1: Float
        pt2: Float
        pt3: Float

        Returns
        -------
        max_side: Float
            The triangle face with the largest side
        """
        side_a = np.linalg.norm(pt1 - pt2)
        side_b = np.linalg.norm(pt2 - pt3)
        side_c = np.linalg.norm(pt3 - pt1)
        s = 0.5 * ( side_a + side_b + side_c)

        max_side = max(s * (s - side_a) * 
                (s - side_b) * 
                (s - side_c), 0) ** 0.5

        return max_side


    def sample_point(self, pt1, pt2, pt3):
        """
        Samples and returns one point per triangular face using 
        barycentric coordinates on a triangle

        Ref: https://mathworld.wolfram.com/BarycentricCoordinates.html

        Parameters
        ----------
        pt1: Float
        pt2: Float
        pt3: Float

        Returns
        -------
        f(0): Float
            Sampled point from 1/3 face
        f(1): Float
            Sampled point from 2/3 face
        f(3): Float
            Sampled point from 3/3 face
        """
        s, t = sorted([random.random(), random.random()])

        f = lambda i: s * pt1[i] + (t-s) * pt2[i] + (1-t) * pt3[i]

        return (f(0), f(1), f(2))


    def __call__(self, mesh):
        verts, faces = mesh
        verts = np.array(verts)
        areas = np.zeros((len(faces)))

        for i in range(len(areas)):
            areas[i] = (self.triangle_area(verts[faces[i][0]],
                                           verts[faces[i][1]],
                                           verts[faces[i][2]]))

        sampled_faces = (random.choices(faces,
                                        weights=areas,
                                        cum_weights=None,
                                        k=self.output_size))

        sampled_points = np.zeros((self.output_size, 3))

        for i in range(len(sampled_faces)):
            sampled_points[i] = (self.sample_point(verts[sampled_faces[i][0]],
                                                   verts[sampled_faces[i][1]],
                                                   verts[sampled_faces[i][2]]))

        return sampled_points


class Normalize(object):
    """
    Normalises point clouds

    Parameters
    ----------
    pointcloud: array

    Returns
    -------
    norm_pointcloud: array
        Returns an array of normalised values for pointcloud
    """
    def __call__(self, pointcloud):
        assert len(pointcloud.shape)==2

        norm_pointcloud = pointcloud - np.mean(pointcloud, axis=0) 
        norm_pointcloud /= np.max(np.linalg.norm(norm_pointcloud, axis=1))

        return  norm_pointcloud


class RandRotation_z(object):
    """
    Applies Random Rotation Around Z-Axis

    Parameters
    ----------
    pointcloud object: array

    Returns
    -------
    rot_pointcloud: array
        Returns an array of values for pointcloud after randomly rotating
        around Z Axis
    """
    def __call__(self, pointcloud):
        assert len(pointcloud.shape)==2

        theta = random.random() * 2. * math.pi
        rot_matrix = np.array([[ math.cos(theta), -math.sin(theta),    0],
                               [ math.sin(theta),  math.cos(theta),    0],
                               [0,                             0,      1]])

        rot_pointcloud = rot_matrix.dot(pointcloud.T).T

        return  rot_pointcloud


class RandomNoise(object):
    """
    Inserts random noise from Gaussian distribution

    Parameters
    ----------
    pointcloud obj: array

    Returns
    -------
    noisy_pointcloud: array
        Returns array after being enhanced with random Gaussian noise
    """
    def __call__(self, pointcloud):
        assert len(pointcloud.shape)==2

        noise = np.random.normal(0, 0.02, (pointcloud.shape))
        noisy_pointcloud = pointcloud + noise

        return  noisy_pointcloud


class ToTensor(object):
    """
    Converts array to Pytorch Tensor

    Parameters
    ----------
    pointcloud object: array

    Returns
    -------
    pointcloud: tensor
        Converts numpy array to PyTorch tensor and returns
    """
    def __call__(self, pointcloud):
        assert len(pointcloud.shape)==2

        return torch.from_numpy(pointcloud)