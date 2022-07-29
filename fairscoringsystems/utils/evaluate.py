import numpy as np
from sklearn.metrics import accuracy_score, balanced_accuracy_score

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def format_labels(y):
    
    y_formatted = []

    for labels in y:
        for i in range(len(labels)):
            if labels[i] == 1:
                y_formatted.append(i)

    return y_formatted

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def predict(x, l_lists):

    """
    Returns the predictions of the set of scoring systems for the given entries

    @x : The input features matrix
    @l_lists : The set of scoring systems
    """

    y = []

    for index, sample in enumerate(x):
        scores = []
        for l_list in l_lists:
            scores.append(sum(feature * l_list[j] for j, feature in enumerate(sample)))
        y_pred = []
        for i in range(len(scores)):
            if i == np.argmax(scores):
                y_pred.append(1)
            else:
                y_pred.append(0)
        y.append(y_pred)

    return np.array(y)

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def get_accuracy(x, y, l_lists):
    
    """
    Compute accuracy for the scoring systems : 
    
    @x_test the test set
    @y_test labels of the test set
    @l the matrix of coefficients lambda that represents the scoring systems
    
    return accuracy
    """
    
    y_pred = predict(x, l_lists)
    y = format_labels(y)
    y_pred = format_labels(y_pred)
    accuracy = accuracy_score(y, y_pred)
                
    return accuracy

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def get_balanced_accuracy(x, y, l_lists):

    y_pred = predict(x, l_lists)
    y = format_labels(y)
    y_pred = format_labels(y_pred)
    balanced_accuracy = balanced_accuracy_score(y, y_pred)
                
    return balanced_accuracy

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def get_sparsity(l_lists):

    """
    Return the number of line (sparsity) of all the scoring systems
    """
    
    spar = 0
    for i in range(len(l_lists)):
        for j in range(len(l_lists[i])):
            if l_lists[i][j] != 0:
                spar += 1
    return spar

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def get_overall_misclassification_rate(x, y, l_lists, g1, g2, label):
    
    N = len(x)  
    
    i_g1 = [i for i in range(N) if x[i][g1] == 1]
    
    if g2:
        i_g2 = [i for i in range(N) if x[i][g2] == 1]
    else:
        i_g2 = [i for i in range(N) if x[i][g1] == 0]


    misclassification_g1 = 0
    misclassification_g2 = 0
    
    for i in i_g1:
        scores = []
        for l_list in l_lists:
            scores.append(sum(feature * l_list[j] for j, feature in enumerate(x[i])))
        if (np.argmax(scores) == label and y[i][label] == 0) or (np.argmax(scores) != label and y[i][label] == 1):
            misclassification_g1 += 1

    for i in i_g2:
        scores = []
        for l_list in l_lists:
            scores.append(sum(feature * l_list[j] for j, feature in enumerate(x[i])))
        if (np.argmax(scores) == label and y[i][label] == 0) or (np.argmax(scores) != label and y[i][label] == 1):
            misclassification_g2 += 1

    if i_g1 and i_g2:
        return abs(misclassification_g1/len(i_g1) - misclassification_g2/len(i_g2))
    if i_g1:
        return abs(misclassification_g1/len(i_g1))
    if i_g2:
        return abs(misclassification_g2/len(i_g2))
    return 0

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def get_statistical_parity(x, l_lists, g1, g2, label):
    
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
        scores = []
        for l_list in l_lists:
            scores.append(sum(feature * l_list[j] for j, feature in enumerate(x[i])))
        if np.argmax(scores) == label:
            pos_g1 += 1
            
    for i in i_g2:
        scores = []
        for l_list in l_lists:
            scores.append(sum(feature * l_list[j] for j, feature in enumerate(x[i])))
        if np.argmax(scores) == label:
            pos_g2 += 1

    if i_g1 and i_g2:
        return abs(pos_g1/len(i_g1) - pos_g2/len(i_g2))
    if i_g1:
        return abs(pos_g1/len(i_g1))
    if i_g2:
        return abs(-pos_g2/len(i_g2))
    return 0

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def get_predictive_equality(x, y, l_lists, g1, g2, label):
    
    """
    Compute the predictive_equality of the scoring system between g1 and g2 :    
    
    @x : the test set features
    @y : the test set labels
    @l_lists : the matrix of lambda coefficients that represents the scoring systems
    @g1, g2 : groups to compare
    @label : the class on which to perform the fairness evaluation
    
    return predictive equality
    """

    N = len(x)  
    
    i_g1 = [i for i in range(N) if x[i][g1] == 1 and y[i][label] == 0]
    if g2:
        i_g2 = [i for i in range(N) if x[i][g2] == 1 and y[i][label] == 0]
    else:
        i_g2 = [i for i in range(N) if x[i][g1] == 0 and y[i][label] == 0]

    pos_g1 = 0
    pos_g2 = 0

    for i in i_g1:
        
        scores = []
        for l_list in l_lists:
            scores.append(sum(feature * l_list[j] for j, feature in enumerate(x[i])))
        if np.argmax(scores) == label:
            pos_g1 += 1
            
    for i in i_g2:
        scores = []
        for l_list in l_lists:
            scores.append(sum(feature * l_list[j] for j, feature in enumerate(x[i])))
        if np.argmax(scores) == label:
            pos_g2 += 1

    if i_g1 and i_g2:
        return abs(pos_g1/len(i_g1) - pos_g2/len(i_g2))
    if i_g1:
        return abs(pos_g1/len(i_g1))
    if i_g2:
        return abs(-pos_g2/len(i_g2))
    return 0


"""--------------------------------------------------------------------------------------------------------------------------------------"""

def get_equal_opportunity(x, y, l_lists, g1, g2, label):
    
    """
    Compute the equal_opportunity of the scoring system between g1 and g2 :    
    
    @x : the test set features
    @y : the test set labels
    @l_lists : the matrix of lambda coefficients that represents the scoring systems
    @g1, g2 : groups to compare
    @label : the class on which to perform the fairness evaluation
    
    return equal opportunity
    """

    N = len(x)  
    
    i_g1 = [i for i in range(N) if x[i][g1] == 1 and y[i][label] == 1]
    if g2:
        i_g2 = [i for i in range(N) if x[i][g2] == 1 and y[i][label] == 1]
    else:
        i_g2 = [i for i in range(N) if x[i][g1] == 0 and y[i][label] == 1]

    pos_g1 = 0
    pos_g2 = 0

    for i in i_g1:
        
        scores = []
        for l_list in l_lists:
            scores.append(sum(feature * l_list[j] for j, feature in enumerate(x[i])))
        if np.argmax(scores) == label:
            pos_g1 += 1
            
    for i in i_g2:
        scores = []
        for l_list in l_lists:
            scores.append(sum(feature * l_list[j] for j, feature in enumerate(x[i])))
        if np.argmax(scores) == label:
            pos_g2 += 1

    if i_g1 and i_g2:
        return abs(pos_g1/len(i_g1) - pos_g2/len(i_g2))
    return 0

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def get_equalized_odds(x, y, l_lists, g1, g2, label):
    
    """
    Compute the equalized_odds of the scoring system between g1 and g2
    (note that equalized odds is a conjunction of predictive parity and equal_opportunities) :    
    
    @x : the test set features
    @y : the test set labels
    @l_lists : the matrix of lambda coefficients that represents the scoring systems
    @g1, g2 : groups to compare
    @label : the class on which to perform the fairness evaluation
    
    return equalized odds
    """

    return max(get_predictive_equality(x, y, l_lists, g1, g2, label), get_equal_opportunity(x, y, l_lists, g1, g2, label))

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def get_mean_equalized_odds(x, y, l_lists, g1, g2, label):
    
    """
    Compute the mean_equalized_odds of the scoring system between g1 and g2
    (note that equalized odds is a conjunction of predictive parity and equal_opportunities) :    
    
    @x : the test set features
    @y : the test set labels
    @l_lists : the matrix of lambda coefficients that represents the scoring systems
    @g1, g2 : groups to compare
    @label : the class on which to perform the fairness evaluation
    
    return MEAN equalized odds
    """

    N = len(x)  
    
    N_pe = len([i for i in range(N) if y[i][label] == 0])
    N_eo = len([i for i in range(N) if y[i][label] == 1])

    return (N_pe*get_predictive_equality(x, y, l_lists, g1, g2, label) + N_eo*get_equal_opportunity(x, y, l_lists, g1, g2, label))/N

