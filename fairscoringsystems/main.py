from random import shuffle
import sys
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold

from utils.parameters import parse_config_file
from utils.dataset import format_dataset
from utils.scoring_system import print_scoring_system_multiclass
from utils.evaluate import get_accuracy, get_balanced_accuracy, get_equal_opportunity, get_equalized_odds, get_mean_equalized_odds, get_sparsity, get_overall_misclassification_rate, get_statistical_parity, get_predictive_equality
from utils.initial_solution import get_initial_solution
from utils.cuts import get_inconsistency_cut, remove_inconcsistency
from fairscoringsystems import get_scoring_systems


"""--------------------------------------------------------------------------------------------------------------------------------------"""

def main(dataset_path, labels_name, constraints, objectives, sensitive_groups, sensitive_labels, time_limit, lambda_bound):

    """
    Run FAIRScoringSystems and print the output scoring systems.

    @dataset_path : the path of the dataset to work with (.csv)
    @labels_name : labels column names
    @constraints : a list of constraints for the model
    @objectives : a list of objectives for the model
    @sensitive_groups : sensitives groups column names
    @sensitive_labels : sensitive labels column names
    @time_limit : maximum execution time for each fold
    @lambda_bound : A hard limit on the scoring systems coefficients
    """

    df = pd.read_csv(dataset_path)                                                      # Load dataset
    df_labels, df_features, features_name, x, y, indexes_sgroup, indexes_slabels = format_dataset(
        df, labels_name, sensitive_groups, sensitive_labels)                            # Format the dataset for SLIMulticlassFAIR

    print(len(x))
    maj, acc = get_initial_solution(y)
    x, y = remove_inconcsistency(x, y)
    print(len(x))

    l_lists, execution_time, gap, objective = get_scoring_systems(                      # Run CPLEX to compute the scoring systems
        x, y, constraints, objectives, lambda_bound, indexes_sgroup, indexes_slabels, time_limit, maj, acc, show_progress=True)      

    if not(l_lists):
        return

    print_scoring_system_multiclass(labels_name, features_name, l_lists)                # Print the scoring systems in a human-readable way

    accuracy = get_accuracy(x, y, l_lists)                                              # Get the accuracy of the scoring system
    balanced_accuracy = get_balanced_accuracy(x, y, l_lists)                            # Get the balanced accuracy of the scoring system

    if indexes_sgroup and indexes_slabels:
        omr = []
        sp = []
        pe = []
        eo = []
        eod = []
        meod = []
        for label in indexes_slabels:
            for g in indexes_sgroup:
                omr.append(get_overall_misclassification_rate(
                    x, y, l_lists, g, None, label))
                sp.append(get_statistical_parity(
                    x, l_lists, g, None, label))
                pe.append(get_predictive_equality(
                    x, y, l_lists, g, None, label))
                eo.append(get_equal_opportunity(
                    x, y, l_lists, g, None, label))
                eod.append(get_equalized_odds(
                    x, y, l_lists, g, None, label))
                meod.append(get_mean_equalized_odds(
                    x, y, l_lists, g, None, label))

        overall_misclassification_rate = np.max(omr)
        statistical_parity = np.max(sp)
        predictive_equality = np.max(pe)
        equal_opportunity = np.max(eo)
        equalized_odds = np.max(eod)
        mean_equalized_odds = np.max(meod)

    print(f"optimality_gap : {np.round(gap, 4)}")                                       # Print optimality gap
    print(f"execution_time : {np.round(execution_time, 4)}")                            # Print execution time
    print(f"objective_value : {np.round(objective, 4)}")                                # Print objective value
    print(f"accuracy : {np.round(accuracy, 4)}")                                        # Print accuracy
    print(f"balanced_accuracy : {np.round(balanced_accuracy, 4)}")                      # Print balanced accuracy
    print(f"sparsity : {get_sparsity(l_lists)}")                                        # Print sparsity

    if indexes_sgroup and indexes_slabels:

        print(f"overall_misclassification_rate : {np.round(overall_misclassification_rate, 4)}")
        print(f"statistical_parity : {np.round(statistical_parity, 4)}")
        print(f"predictive_equality : {np.round(predictive_equality, 4)}")
        print(f"equal_opportunity : {np.round(equal_opportunity, 4)}")
        print(f"max_equalized_odds : {np.round(equalized_odds, 4)}")
        print(f"mean_equalized_odds : {np.round(mean_equalized_odds, 4)}")

    return          

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def test(dataset_path, labels_name, constraints, objectives, sensitive_groups, sensitive_labels, time_limit, lambda_bound, n_folds):

    """
    Run FAIRScoringSystems and perform a K-fold testing. Notify the user the following statistics :
    - execution time
    - optimality gap 
    - accuracy
    - balanced accuracy
    - fairness (if sensible groups and labels)

    @dataset_path : the path of the dataset to work with (.csv)
    @labels_name : labels column names
    @constraints : a list of constraints for the model
    @objectives : a list of objectives for the model
    @sensitive_groups : sensitives groups column names
    @sensitive_labels : sensitive labels column names
    @time_limit : maximum execution time for each fold
    @lambda_bound : A hard limit on the scoring systems coefficients
    @n_folds : number of plits for the K-fold
    """

    print(f"dataset : {dataset_path}")
    print(f"labels_name : {labels_name}")
    for key in constraints.keys():
        print(f"{key} : {constraints[key]}")
    for key in objectives.keys():
        print(f"{key} : {objectives[key]}")
    print(f"sensitive_groups : {sensitive_groups}")
    print(f"sensitive_labels : {sensitive_labels}")
    print(f"time_limit : {time_limit}")
    print(f"lambda_bound : {lambda_bound}")
    print(f"n_folds : {n_folds}")

    df = pd.read_csv(dataset_path)                                                          # Load dataset
    df_labels, df_features, features_name, x, y, indexes_sgroup, indexes_slabels = format_dataset(
        df, labels_name, sensitive_groups, sensitive_labels)                                # Format the dataset for SLIMulticlassFAIR

    maj, acc = get_initial_solution(y)
    x, y = remove_inconcsistency(x, y)

    print(f"nb_samples : {len(x)}")
    print(f"nb_features : {len(x[0])}")
    print(f"nb_labels : {len(y[0])}")                                                    

    accuracy_train = balanced_accuracy_train = overall_misclassification_rate_train = statistical_parity_train = predictive_equality_train = equal_opportunity_train = equalized_odds_train = mean_equalized_odds_train = 0
    accuracy_test = balanced_accuracy_test = overall_misclassification_rate_test = statistical_parity_test = predictive_equality_test = equal_opportunity_test = equalized_odds_test = mean_equalized_odds_test = 0                                                            

    kf = KFold(n_splits=n_folds, shuffle=True, random_state=1)                                            # Data spliter 

    execution_time = []
    gap = []
    objective = []
    sparsity = []

    accuracy_train = []
    balanced_accuracy_train = []
    overall_misclassification_rate_train = []
    statistical_parity_train = []
    predictive_equality_train = []
    equal_opportunity_train = []
    equalized_odds_train = []
    mean_equalized_odds_train = []

    accuracy_test = []
    balanced_accuracy_test = []
    overall_misclassification_rate_test = []
    statistical_parity_test = []
    predictive_equality_test = []
    equal_opportunity_test = []
    equalized_odds_test = []
    mean_equalized_odds_test = []

    for train_index, test_index in kf.split(x):

        x_train, x_test = x[train_index], x[test_index]
        y_train, y_test = y[train_index], y[test_index]
        
        l_lists, fold_execution_time, fold_gap, fold_objective = get_scoring_systems(                       # Run CPLEX to compute the scoring systems
            x_train, y_train, constraints, objectives, lambda_bound, indexes_sgroup, indexes_slabels, time_limit, maj, acc, show_progress=False) 

        execution_time.append(fold_execution_time)                                          # Update the mean execution time
        gap.append(fold_gap)                                                                # Update the mean gap
        objective.append(fold_objective)                                                    # Update the mean objective
        sparsity.append(get_sparsity(l_lists))                                              # Update the mean sparsity
        accuracy_train.append(get_accuracy(x_train, y_train, l_lists))                      # Get the train accuracy of the scoring system
        balanced_accuracy_train.append(get_balanced_accuracy(x_train, y_train, l_lists))    # Get the train balanced accuracy of the scoring system
        accuracy_test.append(get_accuracy(x_test, y_test, l_lists))                         # Get the test accuracy of the scoring system
        balanced_accuracy_test.append(get_balanced_accuracy(x_test, y_test, l_lists))       # Get the test balanced accuracy of the scoring system

        if indexes_sgroup and indexes_slabels:

            omr_train = []
            sp_train = []
            pe_train = []
            eo_train = []
            eod_train = []
            meod_train = []

            omr_test = []
            sp_test = []
            pe_test = []
            eo_test = []
            eod_test = []
            meod_test = []

            for label in indexes_slabels:
                for g in indexes_sgroup:   

                    omr_train.append(get_overall_misclassification_rate(x_train, y_train, l_lists, g, None, label))
                    sp_train.append(get_statistical_parity(x_train, l_lists, g, None, label))
                    pe_train.append(get_predictive_equality(x_train, y_train, l_lists, g, None, label))
                    eo_train.append(get_equal_opportunity(x_train, y_train, l_lists, g, None, label))
                    eod_train.append(get_equalized_odds(x_train, y_train, l_lists, g, None, label))
                    meod_train.append(get_mean_equalized_odds(x_train, y_train, l_lists, g, None, label))

                    omr_test.append(get_overall_misclassification_rate(x_test, y_test, l_lists, g, None, label))
                    sp_test.append(get_statistical_parity(x_test, l_lists, g, None, label))
                    pe_test.append(get_predictive_equality(x_test, y_test, l_lists, g, None, label))
                    eo_test.append(get_equal_opportunity(x_test, y_test, l_lists, g, None, label))
                    eod_test.append(get_equalized_odds(x_test, y_test, l_lists, g, None, label))
                    meod_test.append(get_mean_equalized_odds(x_test, y_test, l_lists, g, None, label))

            overall_misclassification_rate_train.append(np.max(omr_train))
            statistical_parity_train.append(np.max(sp_train))
            predictive_equality_train.append(np.max(pe_train))
            equal_opportunity_train.append(np.max(eo_train))
            equalized_odds_train.append(np.max(eod_train))
            mean_equalized_odds_train.append(np.max(meod_train))

            overall_misclassification_rate_test.append(np.max(omr_test))
            statistical_parity_test.append(np.max(sp_test))
            predictive_equality_test.append(np.max(pe_test))
            equal_opportunity_test.append(np.max(eo_test))
            equalized_odds_test.append(np.max(eod_test))
            mean_equalized_odds_test.append(np.max(meod_test))

    print(f"optimality_gap : {gap}")  
    print(f"execution_time : {execution_time}") 
    print(f"objective_function : {objective}")
    print(f"sparsity : {sparsity}")                                
    print(f"accuracy_train : {accuracy_train}")                                      
    print(f"balanced_accuracy_train : {balanced_accuracy_train}")   
    print(f"accuracy_test : {accuracy_test}")                                      
    print(f"balanced_accuracy_test : {balanced_accuracy_test}")                    

    if indexes_sgroup and indexes_slabels:

        print(f"overall_misclassification_rate_train : {overall_misclassification_rate_train}")
        print(f"statistical_parity_train : {statistical_parity_train}")
        print(f"predictive_equality_train : {predictive_equality_train}")
        print(f"equal_opportunity_train : {equal_opportunity_train}")
        print(f"max_equalized_odds_train : {equalized_odds_train}")
        print(f"mean_equalized_odds_train : {mean_equalized_odds_train}")

        print(f"overall_misclassification_rate_test : {overall_misclassification_rate_test}")
        print(f"statistical_parity_test : {statistical_parity_test}")
        print(f"predictive_equality_test : {predictive_equality_test}")
        print(f"equal_opportunity_test : {equal_opportunity_test}")
        print(f"max_equalized_odds_test : {equalized_odds_test}")
        print(f"mean_equalized_odds_test : {mean_equalized_odds_test}")

    print("end")            
    return

"""--------------------------------------------------------------------------------------------------------------------------------------"""

if __name__ == "__main__":
    
    if len(sys.argv) == 2:
        
        params = parse_config_file(sys.argv[1])

        if not(params):
            exit(1)

        dataset_path = params["dataset_path"]
        labels_name = params["labels_name"]
        objectives = params["objectives"]
        constraints = params["constraints"]
        sensitive_groups = params["sensitive_groups"]
        sensitive_labels = params["sensitive_labels"]
        time_limit = params["time_limit"]
        lambda_bound = params["lambda_bound"]
        testing_mode = params["testing_mode"]
        n_folds = params["n_folds"]

        if testing_mode:
            test(dataset_path, labels_name, constraints, objectives,
                 sensitive_groups, sensitive_labels, time_limit, lambda_bound, n_folds)
        else:
            main(dataset_path, labels_name, constraints, objectives,
                 sensitive_groups, sensitive_labels, time_limit, lambda_bound)
    else:
        print("Usage : python main.py <config_file_path>")
