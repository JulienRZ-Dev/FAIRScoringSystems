import pandas as pd

# GLOBAL VARIABLES

parameters = ["dataset_path", "label_name", "sensitive_group", "time_limit", "c_0", "e", "reg", "lambda_bound", "testing_mode", "n_folds"]
df = None

# DEFAULT VALUES 

C0 = 0.01
E = 0.1
REG = False
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

def parse_label(s):
    global df
    try:
        l = s.strip()
        if not(l in df.columns):
            print("[ERROR] : The provided labels does not correspond to the dataset column names")
            return None
        if l:
            return l
        else:
            return None
    except Exception as e:
        return None

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def parse_group(s):
    global df
    try:
        g = s.strip()
        if not(g in df.columns):
            print("[ERROR] : The provided group does not correspond to the dataset column names")
            return None
        if g:
            return g
        else:
            return None
    except Exception as e:
        return None

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

def parse_c0(s):
    if not(s):
        return C0
    try:
        return float(s)
    except:
        print("[ERROR] : incorrect input")
        return None

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def parse_e(s):
    if not(s):
        return E
    try:
        return float(s)
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

def parse_reg(s):
    if not(s):
        return REG
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
        "label_name": "",
        "sensitive_group": "",
        "time_limit": TIME_LIMIT,
        "c_0": C0,
        "e": E,
        "reg": REG,
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
                    print("[ERROR] Wrong key")
                    pass
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
                if key == "label_name":
                    res = parse_label(value)
                    if res != None:
                        response["label_name"] = res
                    else:
                        print("[ERROR] label_name")
                        return None

                # Sensitive group
                if key == "sensitive_group":
                    res = parse_group(value)
                    if res != None:
                        response["sensitive_group"] = res
                    else:
                        print("[ERROR] sensitive_group")
                        return None

                # Time limit
                if key == "time_limit":
                    res = parse_time(value)
                    if res != None:
                        response["time_limit"] = res
                    else:
                        print("[ERROR] time_limit")
                        return None

                # C_0
                if key == "c_0":
                    res = parse_c0(value)
                    if res != None:
                        response["c_0"] = res
                    else:
                        print("[ERROR] c_0")
                        return None

                # E
                if key == "e":
                    res = parse_e(value)
                    if res != None:
                        response["e"] = res
                    else:
                        print("[ERROR] e")
                        return None

                # reg
                if key == "reg":
                    res = parse_reg(value)
                    if res != None:
                        response["reg"] = res
                    else:
                        print("[ERROR] reg")
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