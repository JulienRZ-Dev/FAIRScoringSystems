"""--------------------------------------------------------------------------------------------------------------------------------------"""

def get_class_count(y):

    """
    Get the count for each class in the labels

    return the count of each class
    """

    count = []

    for i in range(len(y[0])):
        count.append(0)

    for labels in y:
        for index, label in enumerate(labels):
            if label == 1:
                count[index] += 1

    return count

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def get_class_indexes(y):

    """
    Get the indexes of each class in the labels

    return the indexes of each class
    """

    indexes = []

    for i in range(len(y[0])):
        indexes.append([])

    for i, labels in enumerate(y):
        for index, label in enumerate(labels):
            if label == 1:
                indexes[index].append(i)

    return indexes

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def select_labels(y, labels):

    """
    Select the sensitives labels from the actual labels

    return the sensitives labels matrix
    """

    ys = []
    for line in y:
        ys.append([line[i] for i in labels])
    return ys