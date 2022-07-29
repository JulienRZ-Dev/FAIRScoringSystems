from cProfile import label
import numpy as np
import pandas as pd

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def get_index_from_name(df, name):
    return df.columns.get_loc(name)

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def format_dataset(df, label_name, sensitive_group):
    
    """
    Format pandas dataframe to clean it, and return numpy arrays
    
    @dataset : the dataset to format (pandas.df)
    @labels_name : The labels name
    @sensitive_groups : the sensitive groups name
    returns features_name, x (features matrix), y (labels matrix)
    """
    
    df.dropna()                                                                                 # SLIM doestn't handle NA
    df.drop_duplicates()                                                                        # Remove duplicates lines for data reduction  
    df.insert(0, "intercept", np.ones(len(df.index)))
    
    features_name = [item for item in df.columns.to_numpy() if item not in label_name]          # Get the features names

    df_label = df[label_name]
    df_features = df[features_name]
        
    y = np.array([-1 if i == 0 else i for i in df_label.to_numpy()])                            # Get the labels as a numpy array (translate 0 to -1 if needed)
    x = df_features.to_numpy().astype(int)                                                      # Get the features as a numpy array                                        
    if(sensitive_group):
        sgroup_index = get_index_from_name(df_features, sensitive_group)                            # Get the indexes of the sensitives groups 
    else :
        sgroup_index = None
    return features_name, x, y, sgroup_index

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def get_columns_from_index(df, index):
    return df.columns[index]
