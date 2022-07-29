# -*- coding: utf-8 -*-

import cplex
from docplex.mp.model import Model
import numpy as np
import pandas as pd

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def get_scoring_system(x, y, lambda_bound, C_0, time_limit, tp_reg=False, epsilon=None, g=None):
    
    """
    Compute the scoring system according to a given dataset and some user parameters :
    
    @x : the dataset features
    @y : the dataset labels
    @lambda_bound : lower and upper bound for the scoring system cofficients
    @C_0 : parameter to balance accuracy and sparsity
    @time_limit : Max CPLEX execution time
    @tp_reg : Automatically balance the importance of tpr and tnr
    @epsilon : Fairness margin  
    @g : group index for the fairness constraint 
    
    returns a list of lambda coefficients that defines the scoring system and the execution time
    """

    N = len(x)                                               # Number of samples in the dataset
    P = len(x[0])                                            # Number of features for a sample in the dataset
    gamma = 0.1                                              # margin parameter
    i_pos = [i for i in range(N) if y[i] == 1]               # Get the positive class indexes
    i_neg = [i for i in range(N) if y[i] == -1]              # Get the negative class indexes
    
    if tp_reg:
        W_pos = np.round(len(i_neg)/N, 4)                    # Balance paramaeter for tpr (round to prevent python weird rounding)
        W_neg = np.round(1 - W_pos, 4)                       # Balance paramaeter for tnr
    else:
        W_pos = 1                                            # Balance paramaeter for tpr (round to prevent python weird rounding)
        W_neg = 1                                            # Balance paramaeter for tnr        


    m = Model(name="SLIMFair")                               # Create the model for SLIM classification with fairness constraints
    m.parameters.threads=1                                   # Set the number of threads
    m.parameters.timelimit = time_limit                      # Set the time limit

    # Variables 
    l_0 = m.integer_var(-lambda_bound, lambda_bound, name="lambda_0")                   # First coefficient for the scoring system
    l = m.integer_var_list(range(1, P), -lambda_bound, lambda_bound, name="lambda_")    # Coefficients for the scoring system
    z = m.binary_var_list(range(N), name="z_")                                          # loss variable (z_i = 1 if a sample is misclassified)
    alpha = m.binary_var_list(range(1, P), name="alpha_")                               # alpha_j = 1 if lambda_j is non-zero

    # 0-1 loss constraint
    for i in range(0, N):
        M = lambda_bound + sum(lambda_bound*x[i][j+1] for j in range(P-1))                                  # Get exact value of big M constant 
        m.add_constraint(M*z[i] >= gamma - y[i]*(l_0 + m.sum(l[j]*x[i][j+1] for j in range(P-1))))          # Loss constraint to get the misclassifications z_i
        m.add_constraint((M*(z[i]-1) <= -gamma - y[i]*(l_0 + m.sum(l[j]*x[i][j+1] for j in range(P-1)))))

    # Sparsity : constraint alpha_j
    for j in range(P-1):
        m.add_constraint(-lambda_bound*alpha[j] <= l[j])
        m.add_constraint(l[j] <= lambda_bound*alpha[j])
        
    # Fairness : parity constraint over g_1 and g_2
    if epsilon and g:
        
        g1 = [i for i in range(N) if x[i][g] == 1]
        g2 = [i for i in range(N) if x[i][g] == 0]
        g1_pos = [i for i in range(N) if (x[i][g] == 1 and y[i] == 1)]
        g1_neg = [i for i in range(N) if (x[i][g] == 1 and y[i] == -1)]
        g2_pos = [i for i in range(N) if (x[i][g] == 0 and y[i] == 1)]
        g2_neg = [i for i in range(N) if (x[i][g] == 0 and y[i] == -1)]
        N_g1 = len(g1)   
        N_g2 = len(g2)       

        # Check if all parameters are set
        if not(epsilon and g):
            print("Usage : provide epsilon margin and group index if you want to include fairness constraints")
            return None, None
        
        # Add fairness constraints
        else:
            m.add_constraint(((1/N_g1)*(sum(1-z[i] for i in g1_pos) + sum(z[i] for i in g1_neg)) - epsilon) 
                        <= (1/N_g2)*(sum(1-z[i] for i in g2_pos) + sum(z[i] for i in g2_pos)))     
            m.add_constraint((1/N_g2)*(sum(1-z[i] for i in g2_pos) + sum(z[i] for i in g2_neg))
                        <= ((1/N_g1)*(sum(1-z[i] for i in g1_pos) + sum(z[i] for i in g1_neg)) + epsilon))
        
    # Objective : minimizing loss and model size
    m.minimize((W_pos/N)*m.sum(z[i] for i in i_pos) + (W_neg/N)*m.sum(z[i] for i in i_neg)     # 0-1 loss on positive and negative class
                + m.sum(C_0*alpha[j] for j in range(P-1)))                                     # Sparsity (sum of non-zero lambdas coefficients)

    # Solve the model and get the lambda coefficients
    sol = m.solve(log_output=False)
    
    # Concatenate l_0 and other l coefficients
    l_list = np.insert(np.array(sol.get_values(l), dtype=int), 0, np.array(sol.get_value(l_0)), axis=0)
    
    # Reduce the coefficients to co-prime integers
    gcd = np.gcd.reduce(l_list)
    l_list = [int(i/gcd) for i in l_list]
    
    # Keep track of few metrics 
    execution_time = m.solve_details.time
    gap = m.solve_details.gap
    objective = sol.get_objective_value()

    return l_list, execution_time, gap, objective