def print_scoring_system_multiclass(labels_name, features_name, l_lists):

    """
    Print the scoring systems according to the features names and the lambda coefficients
    
    @label_names are the name of the labels to print for each the scoring system
    @features_names are the name of the features of the dataset
    @l is the matrix of the coefficients lambda for the scoring systems
    
    is l[i] == 0 then the row is not printed 
    """
    
    for index, l in enumerate(l_lists):
        print("\n")
        print(f"SCORE FOR {labels_name[index]} \n")
        print("*" * 85)
        for i in range(0, len(l)):    
            if(l[i]):
                print("* " + features_name[i] + " ?" + " " * (70 - len(features_name[i]) - len(str(l[i]))) + str(l[i]) + " POINTS   *")
                print("*" * 85)
        print("\n")