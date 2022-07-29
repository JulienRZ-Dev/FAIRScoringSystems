import numpy as np
from sklearn.metrics import accuracy_score

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def predict(x, l_list):

    """
    Returns the prediction of the scoring system for a given sample

    @x : The input features vector
    @l_list : The scoring system
    """

    if sum(feature * l_list[j] for j, feature in enumerate(x)) > 0:
        return 1
    else:
        return 0


"""--------------------------------------------------------------------------------------------------------------------------------------"""
 
def predict_array(x, l_list):

    """
    Returns the prediction of the scoring system for a given array

    @x : The input features matrix
    @l_list : The scoring system
    """

    y = []

    for sample in x:
        if sum(feature * l_list[j] for j, feature in enumerate(sample)) > 0:
            y_pred = 1
        else:
            y_pred = 0

        y.append(y_pred)

    return np.array(y)

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def get_accuracy(x, y, l_list):
    
    """
    Compute accuracy for the scoring system : 
    
    @x_test the features of the test set
    @y_test labels of the test set
    @l_list the array of coefficients lambda that represents the scoring system
    
    return accuracy
    """
    
    y_pred = predict_array(x, l_list)
    y_pred = [-1 if i == 0 else i for i in y_pred]
    accuracy = accuracy_score(y, y_pred)
                
    return accuracy

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def get_sparsity(l_list):

    """
    Return the number of line (sparsity) of the scoring system
    """
    
    spar = 0
    for i in range(len(l_list)):
        if l_list[i] != 0:
            spar += 1
    return spar - 1                 # First line doesn't count

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def get_statistical_parity(x, l_list, g1, g2):
    
    """
    Compute the statistical parity of the scoring system between g1 and g2 :    
    
    @x : the test set features
    @l_lists : the matrix of lambda coefficients that represents the scoring systems
    @g1, g2 : groups to compare
    @label : the class on which to perform the fairness evaluation
    
    return statistical parity
    """

    N = len(x)  
    
    i_g1 = [i for i in range(N) if x[i][g1] == 1]
    if g2:
        i_g2 = [i for i in range(N) if x[i][g2] == 1]
    else:
        i_g2 = [i for i in range(N) if x[i][g1] == 0]

    pos_g1 = 0
    pos_g2 = 0
    
    for i in i_g1:
        pos_g1 += predict(x[i], l_list)
            
    for i in i_g2:
        pos_g2 += predict(x[i], l_list)

    if i_g1 and i_g2:
        return abs(pos_g1/len(i_g1) - pos_g2/len(i_g2))
    if i_g1:
        return abs(pos_g1/len(i_g1))
    if i_g2:
        return abs(-pos_g2/len(i_g2))
    return 0
