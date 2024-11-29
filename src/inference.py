
######################################################## Import required modules ###############################################################


import json
import torch
from transformers import RobertaTokenizer, RobertaForSequenceClassification, RobertaConfig


########################################################### Tools and variables ################################################################

MODEL_NAME = 'model.pth'
PRE_TRAINED_MODEL_NAME = 'roberta-base'
MAX_SEQ_LEN = 128

classes = [0, 1]

# Load Hugging Face Tokenizer
TOKENIZER = RobertaTokenizer.from_pretrained(PRE_TRAINED_MODEL_NAME)  

# SageMaker model input function
def input_fn(serialized_input_data, content_type='application/jsonlines'): 
    return serialized_input_data

# SageMaker model output function
def output_fn(prediction_output, accept='application/jsonlines'):
    return prediction_output, accept


###################################################### SageMaker load model function ###########################################################


# You need to put in config.json from saved fine-tuned Hugging Face model in code/ 
# Reference it in the inference container at /opt/ml/model/code
def model_fn(model_dir):
    model_path = '{}/{}'.format(model_dir, MODEL_NAME) 
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model_config_path = '/opt/ml/model/code/config.json'
    config = RobertaConfig.from_json_file(model_config_path)
    model = RobertaForSequenceClassification.from_pretrained(model_path, config=config)
    model.to(device)
    return model


######################################################## SageMaker predict function ############################################################


def predict_fn(input_data, model):
    model.eval()

    print('input_data: {}'.format(input_data))
    print('type(input_data): {}'.format(type(input_data)))
    
    data_str = input_data.decode('utf-8')
    print('data_str: {}'.format(data_str))
    print('type data_str: {}'.format(type(data_str)))
    
    jsonlines = data_str.split("\n")
    print('jsonlines: {}'.format(jsonlines))
    print('type jsonlines: {}'.format(type(jsonlines)))

    predicted_classes = []

    for jsonline in jsonlines:
        print('jsonline: {}'.format(jsonline))
        print('type jsonline: {}'.format(type(jsonline)))

        # features[0]:  news_body
        # features[1..n]:  is anything else (we can define the order ourselves)
        # Example:  
        #    {"features": ["The best gift ever", "Gift Cards"]}        
        #
        news_body = json.loads(jsonline)["features"][0]
        print("""news_body: {}""".format(news_body))
    
        encode_plus_token = TOKENIZER.encode_plus(
            news_body,
            max_length=MAX_SEQ_LEN,
            add_special_tokens=True,
            return_token_type_ids=False,
            pad_to_max_length=True,
            return_attention_mask=True,
            return_tensors='pt',
            truncation=True)
    
        input_ids = encode_plus_token['input_ids']
        attention_mask = encode_plus_token['attention_mask']

        output = model(input_ids, attention_mask)
        print('output: {}'.format(output))

    
        prediction = output[0].squeeze()

    
        # configure the response dictionary
        prediction_dict = {}
        prediction_dict['prediction'] = prediction.item()

        jsonline = json.dumps(prediction_dict)
        print('jsonline: {}'.format(jsonline))

        predicted_classes.append(jsonline)
        print('predicted_classes in the loop: {}'.format(predicted_classes))

    predicted_classes_jsonlines = '\n'.join(predicted_classes)
    print('predicted_classes_jsonlines: {}'.format(predicted_classes_jsonlines))

    return predicted_classes_jsonlines