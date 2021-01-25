from flask import *
import json
import numpy as np
import hashlib 
import tensorflow as tf
from tensorflow import keras 
import numpy as np 
import matplotlib.pyplot as plot
from flask_mongoengine import MongoEngine
from math import *
import random
import string
from datetime import datetime
from bson.binary import Binary
import pickle
from PIL import Image
import io
from flask_cors import CORS

mongodb_pass = 'gobears'
db_name = 'Main'

app = Flask(__name__)
CORS(app)
db_name = "Main"
DB_URI = "mongodb+srv://s3kim2018:{}@cluster0.nw98u.mongodb.net/{}?retryWrites=true&w=majority".format(mongodb_pass, db_name)
app.config["MONGODB_HOST"] = DB_URI
db = MongoEngine()
db.init_app(app)


class User(db.Document):
    apikey = db.StringField()
    def to_json(self): 
        return {
            "apikey": self.apikey
        } 

class Model(db.Document):
    modelid = db.StringField()
    apikey = db.StringField()
    modelname = db.StringField()
    type = db.StringField()
    description = db.StringField()
    date = db.DateTimeField()
    model = db.StringField()
    def to_json(self):
        return {
            "modelid": self.modelid,
            "apikey": self.apikey,
            "modelname": self.modelname,
            "type": self.type,
            "description": self.description,
            "date": self.date,
            "model": self.model
        }

class Dataset(db.Document):
    datasetid = db.StringField()
    modelid = db.StringField()
    apikey = db.StringField()
    datasetname = db.StringField()
    datatype = db.StringField()
    size = db.StringField()
    imgw = db.StringField()
    imgh = db.StringField()
    def to_json(self):
        return {
            "datasetid": self.datasetid,
            "modelid": self.modelid,
            "apikey": self.apikey, 
            "datasetname": self.datasetname,
            "datatype": self.datatype,
            "size": self.size,
            "imgw": self.imgw,
            "imgh": self.imgh
        }

class Data(db.Document): 
    apikey = db.StringField()
    datasetid = db.StringField()
    node = db.StringField()
    binarynode = db.FileField()
    classification = db.StringField()




# class testset(db.Document):

@app.route('/register', methods = ['GET'])
def register(): #Returns an length 6 api key 
    key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    hashkey = str(hashlib.sha1(key.encode('utf-8')).hexdigest())
    newuser = User(apikey = hashkey)
    newuser.save()
    return jsonify(key)

@app.route('/createmodel', methods = ['PUT'])
def createmodel():
    apikey = request.headers.get('apikey')
    compkey = str(hashlib.sha1(apikey.encode('utf-8')).hexdigest())
    name = str(request.args.get('name'))
    modeltype = str(request.args.get('model'))
    description = str(request.args.get('desc'))
    id = str(request.args.get('id'))
    if Model.objects(modelid = id) or Model.objects(modelname = name):
        return make_response("Model ID or Model Name already exists", 409)
    if User.objects(apikey = compkey):
        network = keras.Sequential().to_json()
        now = datetime.now()
        mod = Model(modelid = id, apikey = compkey, modelname = name, type = modeltype, description = description, date = now, model = network)
        mod.save()
        return make_response("success", 201)
    else: 
        return make_response("Invalid API-KEY", 401)

@app.route('/getmodel', methods = ["GET"])
def getmodel(): 
    apikey = request.headers.get('apikey')
    id = str(request.args.get('id'))
    compkey = str(hashlib.sha1(apikey.encode('utf-8')).hexdigest())

    if User.objects(apikey = compkey):
        if Model.objects(modelid = id, apikey = compkey):
            val = Model.objects(modelid = id, apikey = compkey).first()
            lst = {"ModelID":val.modelid, "ModelName":val.modelname, "ModelType":val.type, "ModelDesc":val.description, "ModelDate":val.date}
            return make_response(jsonify(lst), 200)
        else:
            return make_response("Cannot find model with name: " + str(name), 400)
    else:
        return make_response("Invalid API-KEY", 401)

@app.route('/getallmodels', methods = ["GET"])
def getall():
    apikey = request.headers.get('apikey')
    compkey = str(hashlib.sha1(apikey.encode('utf-8')).hexdigest())
    if User.objects(apikey = compkey):
        retset = []
        if Model.objects(apikey = compkey):
            val = Model.objects(apikey = compkey)
            for v in val.all():
                lst = {"ModelID":v.modelid, "ModelName":v.modelname, "ModelType":v.type, "ModelDesc":v.description, "ModelDate":v.date}
                retset.append(lst)
            return make_response(jsonify(retset), 200)
        else:
            return make_response(jsonify([]), 400)
    else: 
        return make_response("Invalid API-KEY", 401)

@app.route('/editmodel', methods = ["POST"])
def editmodel(): 
    apikey = request.headers.get('apikey')
    compkey = str(hashlib.sha1(apikey.encode('utf-8')).hexdigest())
    name = str(request.args.get('name'))
    description = str(request.args.get('desc'))
    id = str(request.args.get('id'))
    if User.objects(apikey = compkey):
        if Model.objects(apikey = compkey, modelid = id):
            val =  Model.objects(modelid = id, apikey = compkey).first()
            val.modelname = name
            val.description = description
            val.save()
            return make_response("Success", 202)
        else:
            return make_response("Cannot find model associated with model id: " + str(id), 400)
    else: 
        return make_response("Invalid API-KEY", 401)

@app.route('/appendembeddinglayer', methods = ["POST"])
def appendembeddinglayer(): 
    apikey = request.headers.get('apikey')
    compkey = str(hashlib.sha1(apikey.encode('utf-8')).hexdigest())
    id = str(request.args.get('modelid'))
    name = str(request.args.get('name'))
    if 'embedding' not in name:
        return make_response("Embedding layers must have 'embedding' in its name", 406)
    if User.objects(apikey = compkey):
        if Model.objects(apikey = compkey, modelid = id):
            inputdim = request.args.get('input_dim')
            outputdim = request.args.get('output_dim')
            inputlen = request.args.get('input_len')
            if inputdim.isnumeric() and outputdim.isnumeric() and inputlen.isnumeric():
                inputdim = int(inputdim); outputdim = int(outputdim)
            else: 
                return make_response("Input & Output Dimensions and Input Length must be numbers", 406)
            mask_zero = str(request.args.get('mask_zero'))
            val = Model.objects(modelid = id, apikey = compkey).first()
            loaded_model = tf.keras.models.model_from_json(val.model)
            if mask_zero == 'false':
                loaded_model.add(tf.keras.layers.Embedding(inputdim, outputdim, input_length=inputlen, mask_zero = False, name = name))
                val.model = loaded_model.to_json()
                val.save()
                return make_response("Success", 202)
            elif mask_zero == 'true':
                loaded_model.add(tf.keras.layers.Embedding(inputdim, outputdim, input_length=inputlen, mask_zero = True, name = name))
                val.model = loaded_model.to_json()
                val.save()
                return make_response("Success", 202)
            else: 
                return make_response("Mask Zero must be True or False", 406)
        else:
            return make_response("Cannot find model associated with model id: " + str(id), 400)
    else:
        return make_response("Invalid API-KEY", 401)

@app.route('/appenddenselayer', methods = ["POST"])
def appenddenselayer():
    apikey = request.headers.get('apikey') 
    id = str(request.args.get('modelid'))
    compkey = str(hashlib.sha1(apikey.encode('utf-8')).hexdigest())
    name = str(request.args.get('name'))
    if 'dense' not in name: 
        return make_response("Dense layers must have 'dense' in its name", 406)
    if User.objects(apikey = compkey):
        if Model.objects(apikey = compkey, modelid = id):
            units = request.args.get('units')
            if units.isnumeric():
                units = int(units)
            else: 
                return make_response("Units Must be of type Integer", 406)
            act = str(request.args.get('activation'))
            bias = str(request.args.get('use_bias'))
            if not (act == 'relu' or act == 'sigmoid' or act == 'softmax' or act == 'softplus' or act == 'softsign' or act == 'tanh' or act == 'selu' or act == 'elu' or act == 'exponential'):
                return make_response("Invalid Activation Function", 406)

            val = Model.objects(modelid = id, apikey = compkey).first()
            jsonmodel = val.model
            loaded_model = tf.keras.models.model_from_json(jsonmodel)
            if bias == 'false':
                try:
                    loaded_model.add(tf.keras.layers.Dense(units, name = name, activation = act, use_bias = False))
                    updated = loaded_model.to_json()
                    val.model = updated
                    val.save()
                    return make_response("Success", 202)
                except:
                    return make_response("Error Appending the layer, check for duplicate names.", 406) 
            elif bias == 'true':
                try:
                    loaded_model.add(tf.keras.layers.Dense(units, name = name, activation = act, use_bias = True))
                    updated = loaded_model.to_json()
                    val.model = updated
                    val.save()
                    return make_response("Success", 202)
                except: 
                    return make_response('Error Appending the layer, check for duplicate names.', 406) 

            else:
                return make_response("Bias must be true or false", 406)
        else:
            return make_response("Cannot find model associated with model id: " + str(id), 400)

    else:
        return make_response("Invalid API-KEY", 401)

@app.route('/appendflattenlayer', methods = ["POST"])
def appendflattenlayer():
    apikey = request.headers.get('apikey') 
    id = str(request.args.get('modelid'))
    compkey = str(hashlib.sha1(apikey.encode('utf-8')).hexdigest())
    name = str(request.args.get('name'))
    if 'flatten' not in name:
        return make_response("Flatten layers must have 'flatten' in its name", 406)
    if User.objects(apikey = compkey):
        if Model.objects(apikey = compkey, modelid = id):
            val = Model.objects(modelid = id, apikey = compkey).first()
            loaded_model = tf.keras.models.model_from_json(val.model)
            try:
                loaded_model.add(tf.keras.layers.Flatten())
                val.model = loaded_model.to_json()
                val.save()
                return make_response("Success", 202)
            except:
                return make_response('Error Appending the layer, check for duplicate names.', 406) 

        else:
            return make_response("Cannot find model associated with model id: " + str(id), 400)
    else:
        return make_response("Invalid API-KEY", 401)

@app.route('/poplayer', methods = ["DELETE"])
def poplayer():
    apikey = request.headers.get('apikey') 
    id = str(request.args.get('modelid'))
    compkey = str(hashlib.sha1(apikey.encode('utf-8')).hexdigest()) 
    if User.objects(apikey = compkey):
        if Model.objects(apikey = compkey, modelid = id):
            val = Model.objects(modelid = id, apikey = compkey).first()
            jsonmodel = val.model
            loaded_model = tf.keras.models.model_from_json(jsonmodel)
            if len(loaded_model.layers) > 0:
                print(loaded_model.layers)
                loaded_model.pop()
                print(loaded_model.layers)
                val.model = loaded_model.to_json()
                val.save()
                return make_response("Success", 202)
            else: 
                return make_response("No layers to pop", 406)
        else:
            return make_response("Cannot find model associated with model id: " + str(id), 400)

    else:
        return make_response("Invalid API-KEY", 401)

@app.route('/getlayers', methods = ["GET"])
def getlayers():
    apikey = request.headers.get('apikey') 
    id = str(request.args.get('modelid'))
    compkey = str(hashlib.sha1(apikey.encode('utf-8')).hexdigest())
    if User.objects(apikey = compkey):
        if Model.objects(apikey = compkey, modelid = id):
            val = Model.objects(modelid = id, apikey = compkey).first()
            jsonmodel = val.model
            loaded_model = tf.keras.models.model_from_json(jsonmodel)
            dic = dict()
            for layer in loaded_model.layers:
                print(layer.name)
                if 'dense' in layer.name:
                    dic[layer.name] = {'units':layer.units, 'activation':str(layer.activation).split(' ')[1], 'usebias':layer.use_bias}
                elif 'embedding' in layer.name:
                    dic[layer.name] = {'input_dim':layer.input_dim, 'output_dim': layer.output_dim, 'input_len': layer.input_length, 'mask_zero': layer.mask_zero}
                elif 'flatten' in layer.name:
                    dic[layer.name] = "This is a flatten layer"

            return make_response(jsonify(dic), 200)

        else:
            return make_response("Cannot find model associated with model id: " + str(id), 400)
    else: 
        return make_response("Invalid API-KEY", 401)




@app.route('/deletemodel', methods = ["DELETE"])
def deletemodel(): 
    apikey = request.headers.get('apikey')
    id = str(request.args.get('id'))
    compkey = str(hashlib.sha1(apikey.encode('utf-8')).hexdigest())
    if User.objects(apikey = compkey):
        if Model.objects(apikey = compkey, modelid = id):
            val =  Model.objects(modelid = id, apikey = compkey).first()
            val.delete()
            return make_response("Success", 202)
        else:
            return make_response("Cannot find model associated with model id: " + str(id), 400)
    else: 
        return make_response("Invalid API-KEY", 401)


@app.route('/createdataset', methods = ["PUT"])
def createdataset():
    apikey = request.headers.get('apikey')
    compkey = str(hashlib.sha1(apikey.encode('utf-8')).hexdigest())
    if User.objects(apikey = compkey):
        datasetid = str(request.args.get('datasetid'))
        modelid = str(request.args.get('modelid'))
        datasetname = str(request.args.get('datasetname'))
        datatype = str(request.args.get('datatype'))
        if datatype == 'img':
            width = str(request.args.get('imgw'))
            height = str(request.args.get('imgh'))
        if not Model.objects(modelid = modelid, apikey = compkey):
            return make_response("Model ID associated with APIkey not found", 404)
        if Dataset.objects(datasetname = datasetname) or Dataset.objects(datasetid = datasetid):
            return make_response("Dataset ID or Dataset Name already exists", 409)
        if datatype != 'img':
            val = Dataset(datasetid = datasetid, modelid = modelid, apikey = compkey, datasetname = datasetname, datatype = datatype, size = '0')
            val.save()
            return make_response("Success", 201)
        else:
            val = Dataset(datasetid = datasetid, modelid = modelid, apikey = compkey, datasetname = datasetname, datatype = datatype, size = '0', imgw = width, imgh = height)
            val.save()
            return make_response("Success", 201)
    else:
        return make_response("Invalid API-KEY", 401)

@app.route('/adddata', methods = ["PUT"])
def adddata(): 
    apikey = request.headers.get('apikey')
    compkey = str(hashlib.sha1(apikey.encode('utf-8')).hexdigest())
    if User.objects(apikey = compkey):
        datasetid = str(request.args.get('datasetid'))
        classif = str(request.args.get('classification'))
        if (Dataset.objects(apikey = compkey, datasetid = datasetid)):
            val = Dataset.objects(apikey = compkey, datasetid = datasetid).first() 
            datatype = val.datatype
            if datatype == "int" or datatype == "str":
                data = str(request.args.get('data'))
                if data == 'None' or classif == 'None':
                    return make_response("Data or Classification not found", 404)
                val = Data(apikey = compkey, datasetid = datasetid, node = data, classification = classif)
                return make_response("Success", 201)
            else:
                binary = request.get_data()
                print(classif)
                if len(binary) < 3 or classif == 'None':
                    return make_response("Image or Classification not found", 404)
                else:
                    val = Data(apikey = compkey, datasetid = datasetid, binarynode = binary, classification = classif)
                    val.save()
                # img = Image.open(io.BytesIO(binary))
                # img_np = np.array(img)
                return make_response("Success", 201)
        else:
            return make_response("Dataset associated with the datasetid not found", 404)
    else:
        return make_response("Invalid API-KEY", 401)



    




if __name__ == '__main__':
    app.run(debug = True)