import numpy as np
import pandas as pd

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def get_indexes_from_names(df, names):
    indexes = []
    for item in names:
        indexes.append(df.columns.get_loc(item))
    return indexes

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def format_dataset(df, labels_name, sensitive_groups, sensitive_labels):
    
    """
    Format pandas dataframe to clean it, and return numpy arrays
    
    @dataset : the dataset to format (pandas.df)
    @labels_name : The labels name
    @sensitive_groups : the sensitive groups name
    @sensitive_labels : the sensitive labels name
    returns features_name, x (features matrix), y (labels matrix)
    """
    
    df.dropna()                                                                                # SLIM doestn't handle NA
    df.drop_duplicates()                                                                       # Remove duplicates lines for data reduction  
    df.insert(0, "starts with", np.ones(len(df.index)))
    
    features_name = [item for item in df.columns.to_numpy() if item not in labels_name]        # Get the features names

    df_labels = df[labels_name]
    df_features = df[features_name]
        
    y = df_labels.to_numpy()                                                                    # Get the labels as a numpy array
    x = df_features.to_numpy()                                                                  # Get the features as a numpy array                                        
    sgroup_indexes = get_indexes_from_names(df_features, sensitive_groups)                      # Get the indexes of the sensitives groups 
    slabels_indexes = get_indexes_from_names(df_labels, sensitive_labels)                       # Get the indexes of the sensitives labels 
    return df_labels, df_features, features_name, x, y, sgroup_indexes, slabels_indexes

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def get_columns_from_index(df, index):
    return df.columns[index]
