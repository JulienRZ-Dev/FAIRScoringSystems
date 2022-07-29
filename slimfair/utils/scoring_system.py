def reduce_name(name, max_size):
    
    """
    Reduce the size of a name if it's too long
    
    @name the string to reduce
    @max_size the maximum length allowed
    """
    
    reduced_name = name
    if len(name) > max_size:
        reduced_name = name[0:max_size]
    return reduced_name

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def print_scoring_system(features_names, label_name, l):

    """
    Print the scoring system according to the features names and the lambda coefficients
    
    @row_names are the name of the features to print in the scoring system, the first row is the label
    @l is the list of the coefficients lambda for the scoring system
    
    is l[i] == 0 then the row is not printed 
    """
    
    row_names_reduced = [reduce_name(name, 62) for name in features_names]
    print(f"PREDICT {label_name} IF SCORE > {-l[0]}\n")
    print("*" * 85)
    for i in range(1, len(l)):
        if(l[i]):
            print("* " + row_names_reduced[i] + " ?" + " " * (70 - len(row_names_reduced[i]) - len(str(l[i]))) + str(l[i]) + " POINTS   *")
            print("*" * 85)
