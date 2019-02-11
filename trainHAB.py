# A file to perform machine learning on HAB data
#
# Copyright: (c) 2019 Paul Hill

"""
This file contains a script that inputs the configuration file and then
extracts a whole dataset of HAB datacube data.  An available list of ML
classifiers are available to classify the outputs previously extracted
bottleneck features.

By default it loads the configuration file classifyHAB1.xml.  However it can
take one argument that specifies the config file to use i.e.
python3 trainHAB.py classifyHAB3.xml
"""

from keras.callbacks import TensorBoard, ModelCheckpoint, EarlyStopping, CSVLogger
from models import ResearchModels
from dataHAB import DataSet
import time
import os.path
import sys
import numpy as np
from sklearn.svm import SVC
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import StratifiedKFold
from inputXMLConfig import inputXMLConfig
from sklearn.preprocessing import MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

import xgboost as xgb

# Train the model
def train(inDir, dataDir,data_type, seqName, seq_length, model, image_shape,
          batch_size, nb_epoch, featureLength):

    checkpointer = ModelCheckpoint(
        filepath=os.path.join(dataDir, 'checkpoints', model + '-' + data_type + \
            '.{epoch:03d}-{val_loss:.3f}.hdf5'), verbose=1, save_best_only=True)
    # Helper: TensorBoard
    tb = TensorBoard(log_dir=os.path.join(dataDir, 'logs', model))

    # Helper: Stop when we stop learning.
    early_stopper = EarlyStopping(monitor='val_acc', patience=2,  mode='auto')

    # Helper: Save results.
    timestamp = time.time()
    csv_logger = CSVLogger(os.path.join(dataDir, 'logs', model + '-' + 'training-' + \
        str(timestamp) + '.log'))

    data = DataSet(seqName, seq_length, inDir, dataDir)

    # Get samples per epoch.
    # Multiply by 0.7 to attempt to guess how much of data.data is the train set.
    steps_per_epoch = (len(data.data) * 0.7) // batch_size

    #X, Y = data.get_all_sequences_in_memory('train', data_type)
    X, Y, X_test, Y_test = data.get_all_sequences_in_memory2( data_type, 0.2)


    if model == 'RF':
        YI = np.int64(Y)
        Y_testI = np.int64(Y_test)
        fX = X.reshape(X.shape[0], seq_length*featureLength)
        fX_test = X_test.reshape(X_test.shape[0], seq_length*featureLength)

        #scaling = MinMaxScaler(feature_range=(-1,1)).fit(fX)
        #fX = scaling.transform(fX)
        #fX_test = scaling.transform(fX_test)
        rf=RandomForestClassifier(n_estimators=1000,
                                              criterion='entropy',
                                              max_depth=14,
                                              max_features='auto',
                                              random_state=42)

        ## This line instantiates the model.
        #param_grid = {
        #    'n_estimators': [900, 1100],
        #    'max_features': ['auto', 'sqrt', 'log2'],
        #    'max_depth' : [16,18,20,22],
        #    'criterion' :['gini', 'entropy']
        #}

        #rf = GridSearchCV(estimator=rf, param_grid=param_grid, cv= 5)
        ## Fit the model on your training data.
        rf.fit(fX, YI[:,1])

        ## And score it on your testing data.
        rfScore = rf.score(fX_test, Y_testI[:,1])
        np.savetxt('rfImports2.txt', rf.feature_importances_);
        print("RF Score = %f ." % rfScore)

    if model == 'xgb':
        # Train xgboost
        YI = np.int64(Y)
        Y_testI = np.int64(Y_test)
        fX = X.reshape(X.shape[0], seq_length*featureLength)
        fX_test = X_test.reshape(X_test.shape[0], seq_length*featureLength)

        dtrain = xgb.DMatrix(fX, YI)
        dtest = xgb.DMatrix(fX_test, Y_testI)
        param = {'max_depth' : 3, 'eta' : 0.1, 'objective' : 'binary:logistic', 'seed' : 42}
        num_round = 50
        bst = xgb.train(param, dtrain, num_round, [(dtest, 'test'), (dtrain, 'train')])

        preds = bst.predict(dtest)
        preds[preds > 0.5] = 1
        preds[preds <= 0.5] = 0
        print(accuracy_score(preds, Y_testI), 1 - accuracy_score(preds, Y_testI))

    if model == 'svm':
        #Currently, SVMs do not work for very large bottleneck features.
        #tuned_parameters = [{'kernel': ['rbf'], 'gamma': [1e-2, 1e-3, 1e-4, 1e-5],
        #             'C': [0.001, 0.10, 0.1, 10, 25, 50, 100, 1000]}]

        tuned_parameters = [{'kernel': ['rbf'], 'gamma': [1e-2,  1e-4],
                     'C': [0.10,  10, 50, 1000]}]


        YI = np.int64(Y)
        Y_testI = np.int64(Y_test)

        #Cs = [0.001, 0.01, 0.1, 1, 10]
        Cs = [0.01, 0.1]
        #gammas = [0.001, 0.01, 0.1, 1]
        gammas = [0.01, 0.1]
        param_grid = {'C': Cs, 'gamma' : gammas}
        clf = GridSearchCV(SVC(kernel='rbf'), param_grid, cv=2)


#       clf = GridSearchCV(SVC(C=1), tuned_parameters, cv=3)
        #clf = SVC(C=1)
        # scoring='%s_macro' % score)
        fX = X.reshape(X.shape[0], seq_length*featureLength)
        #rm = ResearchModels(model, seq_length, None, features_length=featureLength)

        pca = PCA(n_components=10000)
        pca.fit(fX)


        scaling = MinMaxScaler(feature_range=(-1,1)).fit(fX)
        fX = scaling.transform(fX)
        fX = pca.transform(fX)
        fX_test = X_test.reshape(X_test.shape[0], seq_length*featureLength)
        fX_test = scaling.transform(fX_test)
        fX_test = pca.transform(fX_test)


        clf.fit(fX, YI[:,1])

        svmScore = clf.score(fX_test, Y_testI[:,1])
        print("SVM score =  %f ." % svmScore)
    else:
        # Get the model.
        rm = ResearchModels(model, seq_length, None,features_length=featureLength)
        rm.model.fit(
                X,
                Y,
                batch_size=batch_size,
                #validation_data=(X_test, Y_test),
                validation_split=0.1,
                verbose=1,
                callbacks=[tb, early_stopper, csv_logger],
                epochs=nb_epoch)

        scores = rm.model.evaluate(X_test, Y_test, verbose=1)
        print("%s: %.2f%%" % (rm.model.metrics_names[1], scores[1]*100))

# Cross Validated Version of Train
def trainCV(inDir, dataDir,data_type, seqName, seq_length, model, image_shape,
          batch_size, nb_epoch, featureLength):
    """Set up training"""
    seed = 7
    checkpointer = ModelCheckpoint(
        filepath=os.path.join(dataDir, 'checkpoints', model + '-' + data_type + \
            '.{epoch:03d}-{val_loss:.3f}.hdf5'), verbose=1, save_best_only=True)
    # Helper: TensorBoard
    tb = TensorBoard(log_dir=os.path.join(dataDir, 'logs', model))

    # Helper: Stop when we stop learning.
    early_stopper = EarlyStopping(monitor='val_loss', patience=5, verbose =1)

    # Helper: Save results.
    timestamp = time.time()
    csv_logger = CSVLogger(os.path.join(dataDir, 'logs', model + '-' + 'training-' + \
        str(timestamp) + '.log'))

    data = DataSet(seqName, seq_length, inDir, dataDir)

    # Get samples per epoch.
    # Multiply by 0.7 to attempt to guess how much of data.data is the train set.
    steps_per_epoch = (len(data.data) * 0.7) // batch_size

    X, Yhot = data.get_all_sequences_in_memory('all', data_type)

    Y = Yhot[:,1]

    kfold = StratifiedKFold(n_splits=3, shuffle=True, random_state=seed)
    cvscores = []

    """Loop through Train and Test CV Datasets"""
    for train, test in kfold.split(X, Y):

        X_train =     X[train]
        X_test =      X[test]

        """Choose between SVM and other Models"""
        if model == 'svm':
            Y_train  =    Y[train]
            Y_test  =     Y[test]

            tuned_parameters = [{'kernel': ['rbf'], 'gamma': [1e-2, 1e-3, 1e-4, 1e-5],
                     'C': [0.001, 0.10, 0.1, 10, 25, 50, 100, 1000]}]

            clf = GridSearchCV(SVC(C=1), tuned_parameters, cv=5, verbose=2)
                      # scoring='%s_macro' % score)
            fX_train = X_train.reshape(X_train.shape[0], seq_length*featureLength)

            clf.fit(fX_train, Y_train)
            fX_test =  X_test.reshape(X_test.shape[0], seq_length*featureLength)
            svmScore = clf.score(fX_test, Y_test)
            print("SVM score =  %f ." % svmScore)
            cvscores.append(svmScore * 100)
        else:

            Y_train  =    Yhot[train]
            Y_test  =     Yhot[test]
            rm = ResearchModels(model, seq_length, None, features_length=featureLength)

            rm.model.fit(
                X_train,
                Y_train,
                batch_size=batch_size,
                validation_split=0.33,
                verbose=1,
                callbacks=[tb, early_stopper, csv_logger],
                epochs=nb_epoch)
            scores = rm.model.evaluate(X_test, Y_test, verbose=1)
            print("%s: %.2f%%" % (rm.model.metrics_names[1], scores[1]*100))
            cvscores.append(scores[1] * 100)
    print("%.2f%% (+/- %.2f%%)" % (numpy.mean(cvscores), numpy.std(cvscores)))
    print(cvscores)


"""Main Thread"""
def main(argv):
    """Settings Loaded from Xml Configuration"""
    # model can be one of lstm, mlp, svm
    import pudb; pu.db

    if (len(argv)==0):
        xmlName = 'classifyHAB1.xml'
    else:
        xmlName = argv[0]

    cnfg = inputXMLConfig(xmlName)
    train(cnfg.inDir, cnfg.dataDir, 'features', cnfg.seqName, cnfg.seqLength, cnfg.model, None,
          cnfg.batchSize, cnfg.epochNumber, cnfg.featureLength)
    #train(inDir, dataDir, 'features', seqName, seqLength, model, None,
    #      batchSize, epochNumber, featureLength)

if __name__ == '__main__':
    main(sys.argv[1:])
