import numpy as np

def process_y(y):
    y_processed = []
    for line in y:
        for i in range(len(line)):
            if line[i] == 1:
                y_processed.append(i)
    return y_processed

def get_majority_class(y):
    y = np.array(y).flatten()
    most_common_item = max(y, key = y.tolist().count)
    acc = np.count_nonzero(y == most_common_item) / len(y)
    return most_common_item, acc

def get_initial_solution(y):
    y_processed = process_y(y)
    return get_majority_class(y_processed)