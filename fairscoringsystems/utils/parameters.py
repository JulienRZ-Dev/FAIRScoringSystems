import pandas as pd

# GLOBAL VARIABLES

parameters = ["dataset_path", "labels_name", "objectives", "constraints", "sensitive_groups", "sensitive_labels", "time_limit", "lambda_bound", "testing_mode", "n_folds"]
available_objectives_constraints = ["a", "ba", "s", "omr", "sp", "pe", "eo", "eod"]
df = None

# DEFAULT VALUES 

OBJECTIVES = {}
CONSTRAINTS = {}
SENSITIVE_LIST = []
TIME_LIMIT = 360
LAMBDA_BOUND = 9
TESTING_MODE = False
N_FOLDS = 5

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def parse_dataset(s):
    global df
    if s.endswith('.csv'):
        try:
            df = pd.read_csv(s)
            return s
        except:
            print("[ERROR] : The provided dataset path is not correct")
            return None
    return None

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def parse_labels(s):
    global df
    res = []
    try:
        l = s.strip().split(",")
        for item in l:
            item = item.strip()
            if not(item in df.columns):
                print("[ERROR] : At least one of the provided labels does not correspond to the dataset column names")
                return None
            if item:
                res.append(item)
            else:
                return None
        return res
    except Exception as e:
        return None

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def parse_sensitive_list(s):

    if not(s):
        return SENSITIVE_LIST
    res = []
    try:
        l = s.strip().split(",")
        for item in l:
            if item:
                res.append(item.strip())
            else:
                print("[ERROR] : list is not correclty formated")
                return None
        return res
    except Exception as e:
        print("[ERROR] : list is not correclty formated")
        return None 

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def parse_objectives(s):

    if not(s):
        return OBJECTIVES
    try:
        res= {}
        l=[]
        if not("," in s):
            l.append(s.strip())
        else:
            l = s.strip().split(",")
        for item in l:
            if ":" in item:
                key = item.split(":")[0].strip()
                value = float(item.split(":")[1].strip())
            else:
                key = item.strip()
                value = 1.0
            if not(key in available_objectives_constraints):
                print("[ERROR] : At least one of the given objectives is not valid")
                return None
            if key and value:
                res[key] = value
            else:
                print("[ERROR] : objectives are not correclty formated")
                return None
        return res
    except Exception as e:
        print("[ERROR] : objectives are not correclty formated")
        return(None)

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def parse_constraints(s):

    if not(s):
        return CONSTRAINTS
    try:
        res= {}
        l=[]
        if not("," in s):
            l.append(s.strip())
        else:
            l = s.strip().split(",")
        for item in l:
            if ":" in item:
                key = item.split(":")[0].strip()
                value = float(item.split(":")[1].strip())
            else:
                print("[ERROR] : Each constraint must have an associated value")
                return None
            if not(key in available_objectives_constraints):
                print("[ERROR] : At least one of the given constraints is not valid")
                return None
            if key and value:
                res[key] = value
            else:
                print("[ERROR] : constraints are not correclty formated")
                return None
        return res
    except Exception as e:
        print("[ERROR] : constraints are not correclty formated")
        return(None)

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def parse_time(s):
    if not(s):
        return TIME_LIMIT
    try:
        return int(s)
    except:
        print("[ERROR] : incorrect input")
        return None

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def parse_lambda(s):
    if not(s):
        return LAMBDA_BOUND
    try:
        return int(s)
    except:
        print("[ERROR] : incorrect input")
        return None

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def parse_testing_mode(s):
    if not(s):
        return TESTING_MODE
    try:
        return s == "True"
    except:
        print("[ERROR] : incorrect input")
        return None

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def parse_n_folds(s):
    if not(s):
        return N_FOLDS
    try:
        return int(s)
    except:
        print("[ERROR] : incorrect input")
        return None

"""--------------------------------------------------------------------------------------------------------------------------------------"""
"""--------------------------------------------------------------------------------------------------------------------------------------"""

def parse_config_file(file_path):

    """
    Parse the config file to extract the parameters. Notify the user if the file is not correctly formated.
    
    @file_path : the path of the config file

    return the parameters as a dict or None if any error occured 
    """
    
    response = {
        "dataset_path": "",
        "labels_name": "",
        "objectives": OBJECTIVES,
        "constraints": CONSTRAINTS,
        "sensitive_groups": SENSITIVE_LIST,
        "sensitive_labels": SENSITIVE_LIST,
        "time_limit": TIME_LIMIT,
        "lambda_bound": LAMBDA_BOUND,
        "testing_mode": TESTING_MODE,
        "n_folds": N_FOLDS
    }    
    global df
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
        try:
            for line in lines:
                line = line.strip()
                key = line.split("=", 1)[0].strip()
                if not(key in parameters):
                    break
                value = line.split("=", 1)[1].strip()
                
                # Dataset
                if key == "dataset_path":
                    res = parse_dataset(value)
                    if res != None:
                        response["dataset_path"] = res
                    else:
                        print("[ERROR] dataset_path")
                        return None

                # Labels name
                if key == "labels_name":
                    res = parse_labels(value)
                    if res != None:
                        response["labels_name"] = res
                    else:
                        print("[ERROR] labels_name")
                        return None

                # Objectives
                if key == "objectives":
                    res = parse_objectives(value)
                    if res != None:
                        response["objectives"] = res
                    else:
                        print("[ERROR] objectives")
                        return None
                
                # Constraints
                if key == "constraints":
                    res = parse_constraints(value)
                    if res != None:
                        response["constraints"] = res
                    else:
                        print("[ERROR] constraints")
                        return None

                # Sensitive groups
                if key == "sensitive_groups":
                    res = parse_sensitive_list(value)
                    if res != None:
                        response["sensitive_groups"] = res
                    else:
                        print("[ERROR] sensitive_groups")
                        return None

                # Sensitive labels
                if key == "sensitive_labels":
                    res = parse_sensitive_list(value)
                    if res != None:
                        response["sensitive_labels"] = res
                    else:
                        print("[ERROR] sensitive_labels")
                        return None

                # Time limit
                if key == "time_limit":
                    res = parse_time(value)
                    if res != None:
                        response["time_limit"] = res
                    else:
                        print("[ERROR] time_limit")
                        return None

                # Lambda bound
                if key == "lambda_bound":
                    res = parse_lambda(value)
                    if res != None:
                        response["lambda_bound"] = res
                    else:
                        print("[ERROR] lambda_bound")
                        return None

                # testing mode
                if key == "testing_mode":
                    res = parse_testing_mode(value)
                    if res != None:
                        response["testing_mode"] = res
                    else:
                        print("[ERROR] testing_mode")
                        return None

                # N folds
                if key == "n_folds":
                    res = parse_n_folds(value)
                    if res != None:
                        response["n_folds"] = res
                    else:
                        print("[ERROR] n_folds")
                        return None

            return response

        except:
            return None