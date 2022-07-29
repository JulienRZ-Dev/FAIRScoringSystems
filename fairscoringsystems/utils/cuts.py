import numpy as np

def get_inconsistency_cut(x, y):

    """
    Get the numbers of inconsistencies 

    @x : The dataset features
    @y : The dataset labels
    
    return the inconsistency cut (min loss value)
    """

    new_x, new_y = remove_inconcsistency(x, y)

    return len(new_x)/len(x)


def remove_inconcsistency(x, y):
    
    """
    Remove the inconsistencies

    @x : The dataset features
    @y : The dataset labels
    
    return the dataset withtout the inconsistencies
    """

    x = x.tolist()
    y = y.tolist()

    new_x = []
    new_y = []

    for i in range(len(x)):
        target = get_max_y(x[i], x, y)
        if y[i][target] == 1:
            new_x.append(x[i])
            new_y.append(y[i])

    return np.array(new_x), np.array(new_y)


def get_max_y(cur_x, x, y):
    y = [y[i] for i, x in enumerate(x) if x == cur_x]

    counts = [0 for i in range(len(y[0]))]

    for i in range(len(y)):
        y[i] = y[i].index(1)

    for i in range(len(y)):
        counts[y[i]] += 1

    return counts.index(max(counts))



