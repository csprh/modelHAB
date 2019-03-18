# HAB Deep Learning Classifications

This code is for generating classfication scores for HAB databases

There are two basic classification methods:

1. Extract features from each frame with a ConvNet, passing the sequence to an RNN, in a separate network
2. Extract features from each frame with a ConvNet and pass the sequence to an MLP/LSTM/RF system

## Requirements

This code requires you have Keras 2 and TensorFlow 1 or greater installed. Please see the `requirements.txt` file. To ensure you're up to date, run:

`pip install -r requirements.txt`

## Getting the data

The data is extracted using a MATLAB script and deposited into the CNNIms
directory (one png per time stamp).

## Extracting features

For the five models ('lstm0', `lstm1`, 'lstm2', 'mlp1', `mlp2`, 'RF') features are firstly extracted from each png image using the 
`extract\_features.py` script. 

Keras based models
model = lstm0: BEST PERFORMING lstm (Batch normalisation and dropout)
model = lstm1: Dropout
model = lstm2: Batch Normalisation
model = mlp1:  Batch Normalisation
model = mlp2:  Dropout

These models save the model files in [seqName + model] H5 file

Non Keras based models
model = svm: Support Vector Machines (currently not working)
model = xbg: State of the art boosting method
model = RF:  Random Forest


## Training

The actual training (and testing is done using the python file)

trainHAB.py

The training is controlled using the input configuration xml file (e.g. classifyHAB0.xml)
The elements within the configuration file control the training process.  A typical config file is shown below.


```
<confgData>
	<inDir>/home/cosc/csprh/linux/HABCODE/scratch/HAB/CNNIms/florida4/</inDir>
	<dataDir>/home/cosc/csprh/linux/HABCODE/scratch/HAB/DATA4/</dataDir>
	<seqName>NASNetMobileCropTo11</seqName>
	<featureLength>10560</featureLength>
	<SVDFeatLen>-1</SVDFeatLen>
	<model>lstm0</model>
	<seqLength>10</seqLength>
	<batchSize>128</batchSize>
	<epochNumber>500</epochNumber>
</confgData>
```

```
inDir: The directory where the png images are stored
dataDir: The directory where all the data will be output in the training process
seqName:  CNN output name (numpy file format)
featureLength:  Length of the features output from the CNN
SVDFeatLen: Feature length reduction from first stage (-1) to keep the same size
model:  name of model topology: one of mlp1, mlp2, lstm1, lstm2, RF
seqLength: Number of png images in each modality (temporal span)
batchSize: tensorflow control
epochNumber: tensorflow control
```

## Testing

The actual training (and testing is done using the python file)

* **testHAB.py**

* **HABDetectScript.py**   However, the script HABDetectScript.py shows how to chain all the necessary
parts together to get a detection from a lat, lon and date 
i.e. generate datacube, generate images from datacube, extract
features from images and then produce a classification from the features


* **genSingleH5sWrapper.m**: Top level wrapper code to generate H5 file from 
lat, lon and date (inputs all config info and then calls genSingleH5s)

* **outputImagesFromDataCubeScript.m**: Load all configs and call
  outputImagesFromDataCube.m (take H5 datacube and then output images for
feature extraction / classification 

## TODO

- [ ] Create "whole model" with one CNN for each modality (fine tuned)
- [ ] Try removing more layers of the CNNs
- [ ] Mend the SVM botto layer
- [ ] Evaluate the classification performance of each "features"
- [ ] Implment SVD properly

