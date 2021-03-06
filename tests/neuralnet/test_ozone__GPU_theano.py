import os
os.environ["THEANO_FLAGS"] = "mode=FAST_RUN,device=gpu,floatX=float32,lib.cnmem=0.1,exception_verbosity=high,dnn.enabled=False,optimizer=None"
os.environ["KERAS_BACKEND"] = "theano"

import pyaf.tests.neuralnet.test_ozone_GPU as oz

oz.buildModel(iParallel = False);
oz.buildModel(iParallel = True);
