# -*- coding: utf-8 -*-

import sys
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from utils.parameters import parse_config_file
from utils.dataset import format_dataset
from utils.scoring_system import print_scoring_system
from utils.evaluate import get_accuracy, get_sparsity, get_statistical_parity
from slimfair import get_scoring_system


"""--------------------------------------------------------------------------------------------------------------------------------------"""

def main(dataset_path, label_name, sensitive_group, time_limit, c_0, e, reg, lambda_bound):

    """
    Run SLIMFair and print the output scoring systems and few metrics.

    @dataset_path : the path of the dataset to work with (.csv)
    @label_name : label column name
    @sensitive_group : sensitives group column name
    @time_limit : maximum execution time for each fold
    @c_0 : Trade off parameter between accuracy and sparsity
    @lambda_bound : A hard limit on the scoring systems coefficients
    """

    df = pd.read_csv(dataset_path)                                                          # Load dataset                                                  
    features_names, x, y, index_sgroup = format_dataset(df, label_name, sensitive_group)    # Format the dataset for SLIMulticlassFAIR

    l_list, execution_time, gap, objective = get_scoring_system(                            # Run CPLEX to compute the scoring systems
        x, y, lambda_bound, c_0, time_limit, reg, e, index_sgroup)      

    if not(l_list):
        return

    print_scoring_system(features_names, label_name, l_list)                            # Print the scoring systems in a human-readable way

    accuracy = get_accuracy(x, y, l_list)                                               # Get the accuracy of the scoring system

    if index_sgroup:
        statistical_parity = get_statistical_parity(x, l_list, index_sgroup, None)

    if  l_list and execution_time < time_limit:
        print("solution : optimal")                                                     # Print solution state

    if l_list and execution_time >= time_limit:
        print("solution : non_optimal")                                                 # Print solution state

    print(f"optimality_gap : {np.round(gap, 4)}")                                       # Print optimality gap
    print(f"execution_time : {np.round(execution_time, 4)}")                            # Print execution time
    print(f"objective_value : {np.round(objective, 4)}")                                # Print objective value
    print(f"accuracy : {np.round(accuracy, 4)}")                                        # Print accuracy
    print(f"sparsity : {get_sparsity(l_list)}")                                         # Print sparsity

    if index_sgroup:
        print(f"statistical_parity : {np.round(statistical_parity, 4)}")

    return          

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def test(dataset_path, label_name, sensitive_group, time_limit, c_0, e, reg, lambda_bound, n_folds):

    """
    Run SLIMFair and perform a K-fold testing. Notify the user the following statistics :
    - execution time
    - optimality gap 
    - accuracy
    - balanced accuracy
    - fairness (if sensible group is provided)

    @dataset_path : the path of the dataset to work with (.csv)
    @label_name : label column name
    @sensitive_group : sensitives group column name
    @time_limit : maximum execution time for each fold
    @c_0 : Trade off parameter between accuracy and sparsity
    @lambda_bound : A hard limit on the scoring systems coefficients
    @n_folds : number of plits for the K-fold
    """

    print(f"dataset : {dataset_path}")
    print(f"label_name : {label_name}")
    print(f"sensitive_group : {sensitive_group}")
    print(f"time_limit : {time_limit}")
    print(f"lambda_bound : {lambda_bound}")
    print(f"n_folds : {n_folds}")

    df = pd.read_csv(dataset_path)                                                                 # Load dataset
    features_name, x, y, index_sgroup = format_dataset(df, label_name, sensitive_group)            # Format the dataset for SLIMulticlassFAIR

    print(f"nb_samples : {len(x)}")
    print(f"nb_features : {len(x[0])}")                                                 

    accuracy_train = statistical_parity_train = 0
    accuracy_test = statistical_parity_test = 0                                                            

    kf = KFold(n_splits=n_folds, shuffle=True, random_state=1)                                      # Data spliter 

    execution_time = []
    gap = []
    objective = []
    sparsity = []

    accuracy_train = []
    accuracy_test = []

    statistical_parity_train = []
    statistical_parity_test = []
    
    for train_index, test_index in kf.split(x):

        x_train, x_test = x[train_index], x[test_index]
        y_train, y_test = y[train_index], y[test_index]
        
        l_list, fold_execution_time, fold_gap, fold_objective = get_scoring_system(         # Run CPLEX to compute the scoring systems
            x_train, y_train, lambda_bound, c_0, time_limit, reg, e, index_sgroup) 

        execution_time.append(fold_execution_time)                                          # Update the mean execution time
        gap.append(fold_gap)                                                                # Update the mean gap
        objective.append(fold_objective)                                                    # Update the mean objective
        sparsity.append(get_sparsity(l_list))                                               # Update the mean sparsity
        accuracy_train.append(get_accuracy(x_train, y_train, l_list))                       # Get the train accuracy of the scoring system
        accuracy_test.append(get_accuracy(x_test, y_test, l_list))                          # Get the test accuracy of the scoring system

        if index_sgroup:

            statistical_parity_train.append(get_statistical_parity(x_train, l_list, index_sgroup, None))
            statistical_parity_test.append(get_statistical_parity(x_test, l_list, index_sgroup, None)) 


    print(f"optimality_gap : {gap}")  
    print(f"execution_time : {execution_time}") 
    print(f"objective_function : {objective}")
    print(f"sparsity : {sparsity}")                                
    print(f"accuracy_train : {accuracy_train}")
    print(f"accuracy_test : {accuracy_test}")    

    if index_sgroup:

        print(f"statistical_parity_train : {statistical_parity_train}")
        print(f"statistical_parity_test : {statistical_parity_test}")

    print("end")            
    return

"""--------------------------------------------------------------------------------------------------------------------------------------"""

if __name__ == "__main__":
    
    if len(sys.argv) == 2:
        
        params = parse_config_file(sys.argv[1])

        if not(params):
            exit(1)

        dataset_path = params["dataset_path"]
        label_name = params["label_name"]
        sensitive_group = params["sensitive_group"]
        time_limit = params["time_limit"]
        c_0 = params["c_0"]
        e = params["e"]
        reg = params["reg"]
        lambda_bound = params["lambda_bound"]
        testing_mode = params["testing_mode"]
        n_folds = params["n_folds"]

        if testing_mode:
            test(dataset_path, label_name, sensitive_group, time_limit, c_0, e, reg, lambda_bound, n_folds)
        else:
            main(dataset_path, label_name, sensitive_group, time_limit, c_0, e, reg, lambda_bound)
    else:
        print("Usage : python main.py <config_file_path>")
