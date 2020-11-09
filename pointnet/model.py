import torch
import torch.nn as nn
import numpy as np
import torch.nn.functional as F

class Tnet(nn.Module):
    """
    The T-Net Class specified by Qi et al. (2017)
    predicts a N x N transformed matrix
    """
    def __init__(self, k=3):
        super().__init__()
        self.k=k
        self.conv1 = nn.Conv1d(k,64,1)
        self.conv2 = nn.Conv1d(64,128,1)
        self.conv3 = nn.Conv1d(128,1024,1)

        self.fc1 = nn.Linear(1024,512)
        self.fc2 = nn.Linear(512,256)
        self.fc3 = nn.Linear(256,k*k)

        self.bn1 = nn.BatchNorm1d(64)
        self.bn2 = nn.BatchNorm1d(128)
        self.bn3 = nn.BatchNorm1d(1024)
        self.bn4 = nn.BatchNorm1d(512)
        self.bn5 = nn.BatchNorm1d(256)


    def forward(self, input):
        """
        Performs forward pass on the provided input tensor.
        Average Pooling is used to aggregrate and reduce the 
        results. The returned matrix is a transformed (256, 9)
        tensor.
        
        Parameters
        ----------
        input: tensor
            
        Returns
        -------
        matrix: tensor
            Returns a tensor after applying MLP and reducing it 
            via Average Pooling
        """
        bs = input.size(0)

        xb = F.relu(self.bn1(self.conv1(input)))
        xb = F.relu(self.bn2(self.conv2(xb)))
        xb = F.relu(self.bn3(self.conv3(xb)))

        pool = nn.AvgPool1d(xb.size(-1))(xb)
        flat = nn.Flatten(1)(pool)

        xb = F.relu(self.bn4(self.fc1(flat)))
        xb = F.relu(self.bn5(self.fc2(xb)))

        init = torch.eye(self.k, requires_grad=True).repeat(bs,1,1)

        if xb.is_cuda:
            init=init.cuda()
        matrix = self.fc3(xb).view(-1,self.k,self.k) + init

        return matrix


class Transform(nn.Module):
    """
    Two main transformations are core to PointNet.
    This class provides for input and feature transformation
    A 64-dim T-Net is used to align extracted point features after 
    passing through the MLP.
    """

    def __init__(self):
        super().__init__()
        self.input_transform = Tnet(k=3)
        self.feature_transform = Tnet(k=64)

        self.conv1 = nn.Conv1d(3,64,1)
        self.conv2 = nn.Conv1d(64,128,1)
        self.conv3 = nn.Conv1d(128,1024,1)

        self.bn1 = nn.BatchNorm1d(64)
        self.bn2 = nn.BatchNorm1d(128)
        self.bn3 = nn.BatchNorm1d(1024)


    def forward(self, input):
        """
        Performs forward pass on the provided tensors and 
        first performs input transforms. T-Net provides a 
        3x3 transformed matrix.

        Next, feature transformation is performed and here,
        T-Net provides a 64x64 transformed matrix.

        Permutation Invariance is provided by using Average Pooling
        aggregation technique.

        Parameters
        ----------
        input: tensor

        Output
        ------
        matrix3x3: tensor
            3x3 dimensional transformed matrix of inputs
        matrix64x64: tensor
            64x64 dimensional transformed matrix of features
        output: tensor 
            Flattened tensor after Average Pooling on results
        """

        matrix3x3 = self.input_transform(input)
        xb = torch.bmm(torch.transpose(input,1,2),
                matrix3x3).transpose(1,2)
        xb = F.relu(self.bn1(self.conv1(xb)))

        matrix64x64 = self.feature_transform(xb)

        xb = torch.bmm(torch.transpose(xb,1,2),
                matrix64x64).transpose(1,2)

        xb = F.relu(self.bn2(self.conv2(xb)))
        xb = self.bn3(self.conv3(xb))

        xb = nn.AvgPool1d(xb.size(-1))(xb)
        output = nn.Flatten(1)(xb)

        return output, matrix3x3, matrix64x64


class PointNet(nn.Module):
    def __init__(self, classes = 2):
        super().__init__()
        self.transform = Transform()
        self.fc1 = nn.Linear(1024, 512)
        self.fc2 = nn.Linear(512, 256)
        self.fc3 = nn.Linear(256, classes)

        self.bn1 = nn.BatchNorm1d(512)
        self.bn2 = nn.BatchNorm1d(256)

        self.dropout = nn.Dropout(p=0.3)
        self.logsigmoid = nn.LogSigmoid()


    def forward(self, input):
        """
        Performs forward pass on input point cloud tensor, calls 
        required transforms and returns output

        Parameters
        ----------
        input: tensor

        Returns
        -------
        matrix3x3: tensor
            Transformed tensor of input features
        matrix64x64: tensor
            Transformed tensor of features
        output: tensor 
            Flattened, transformed results of input and feature transformation
            followed by Log Sigmoid transformation on output.
        """

        xb, matrix3x3, matrix64x64 = self.transform(input)
        xb = F.relu(self.bn1(self.fc1(xb)))
        xb = F.relu(self.bn2(self.dropout(self.fc2(xb))))
        output = self.fc3(xb)

        return self.logsigmoid(output), matrix3x3, matrix64x64
