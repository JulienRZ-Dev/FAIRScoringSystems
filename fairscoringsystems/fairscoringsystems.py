from docplex.mp.model import Model
from docplex.mp.progress import ProgressListener, ProgressClock
import cplex
import numpy as np
from utils.utils import get_class_count, get_class_indexes

N_THREADS = 1

"""--------------------------------------------------------------------------------------------------------------------------------------"""

def get_scoring_systems(x, y, constraints, objectives, lambda_bound, fairness_groups, fairness_labels, time_limit, maj, acc, show_progress):

    """
    Compute the scoring systems according to a given dataset and some user parameters :
    
    @x : the dataset features
    @y : the dataset labels
    @objectives : the weighted objectives list
    @constraints : the constraints list 
    @lambda_bound : lower and upper bound for the scoring system cofficients
    @fairness_groups : The sensitive groups indexes
    @fairness_labels : The senstive labels indexes 
    @time_limit : max CPLEX execution time
    @maj : index of the majority class to implement the initial solution
    @acc : accuracy of the majority classifier 
    @show_progress : show/hide progress
    
    returns a matrix of lambda coefficients that defines the scoring systems and the execution time
    """

    N = len(x)                                                                          # Number of samples in the dataset
    L = len(y[0])                                                                       # Number of labels in the dataset
    D = len(x[0])                                                                       # Number of features for a sample in the dataset
    gamma = 0.01                                                                        # Margin parameter
    M = lambda_bound*D + 1                                                              # Get an upper bound on the max score 

    if "ba" in objectives:
        N_class = get_class_count(y)                                                    # Get the number of samples in each class
        class_indexes = get_class_indexes(y)                                            # Get the indexes of each class

    m = Model(name="FAIRScoringSystems")                                                # Create the model for SLIMulticlassFAIR
    m.parameters.threads = N_THREADS                                                    # Number of threads is limited for experiments                               
    m.parameters.timelimit = time_limit                                                 # At the time limit, CPLEX return the best solution so far
                

    #---------------------------------------------------------------------------------------------------------------------------------------------#
    #    VARIABLES                                                                                                                                #
    #---------------------------------------------------------------------------------------------------------------------------------------------#
    
    l = [] 
    initial_solution = []                                                               # Lambda matrix
    for i in range(L):                                                                  # Create a lambda list for each label
        l.append(m.integer_var_list(                                                    # Coefficients for each label
            range(D), -lambda_bound, lambda_bound, name="lambda_" + str(i)
        )) 
        for g in fairness_groups:
            m.add_constraint(l[i][g] == 0)                                              # Forbid to use the sensible attribute
        initial_solution.append([0 for i in range(D)])                                  # Construct the initial solution for warm start
        if i == maj:
            initial_solution[i][0] = 1
        
    print(initial_solution)


    z = m.binary_var_list(range(N), name="z")                                           # Loss variable (z_i = 1 if a sample is misclassified)

    if "s" in constraints:
        alpha = []                                                                      # Alpha matrix 
        for i in range(L):                                                              # Create an alpha list for each label
            alpha.append(m.binary_var_list(range(D), name="alpha_" + str(i)))           # alpha_j = 1 if lambda_j is non-zero 

    if "omr" in constraints or "sp" in constraints or "pe" in constraints or "eo" in constraints or "eod" in constraints:
        pos = []                                                                        # Matrix to store the exampels classified as positive
        for i in range(N):                                                              # Create an pos list for each row
            pos.append(m.binary_var_list(range(L), name="pos_" + str(i)))               # pos_i_l = 1 if score_i_l > all_other_scores 


    #---------------------------------------------------------------------------------------------------------------------------------------------#
    #    DECISION VARIABLES MODELING                                                                                                              #
    #---------------------------------------------------------------------------------------------------------------------------------------------#

    if "a" in objectives or "ba" in objectives:
        for i in range(N):                                                              # Constraint z to model misclassifications
            for index in range(L):
                if(y[i][index] == 1):
                    for offset in range(1, L):  
                        m.add_constraint(-M*z[i] <= m.sum(l[index][j]*x[i][j] for j in range(D)) - gamma*index - m.sum(l[(index + offset)%L][j]*x[i][j] for j in range(D)) - gamma*((index + offset)%L))

    if "s" in constraints:
        for index in range(L):                                                          # Constraint alpha to model non-zero lambda coefficients
            for j in range(D):
                m.add_constraint(-lambda_bound*alpha[index][j] <= l[index][j])
                m.add_constraint(l[index][j] <= lambda_bound*alpha[index][j])


    if "omr" in constraints or "sp" in constraints or "pe" in constraints or "eo" in constraints or "eod" in constraints:    
        for i in range(N):
            for index in range(L):
                for offset in range(1, L):                                              # Model number of positive classification for each sensitive class
                    m.add_constraint(-M*(1 - pos[i][index]) <= (m.sum(l[index][j]*x[i][j] for j in range(D)) - gamma*index) 
                                                             - (m.sum(l[(index + offset)%L][j]*x[i][j] for j in range(D)) - gamma*((index+offset)%L))) 
            m.add_constraint(m.sum(pos[i][index] for index in range(L)) == 1)

    #---------------------------------------------------------------------------------------------------------------------------------------------#
    #    WARM START                                                                                                                               #
    #---------------------------------------------------------------------------------------------------------------------------------------------#

    if "omr" in constraints or "sp" in constraints or "pe" in constraints or "eo" in constraints or "eod" in constraints:       # Enable warmstart     
        warmstart = m.new_solution()
        for i in range(L):
            for j in range(D):
                warmstart.add_var_value(l[i][j], initial_solution[i][j])
        m.add_mip_start(warmstart)


    #---------------------------------------------------------------------------------------------------------------------------------------------#
    #    CONSTRAINTS                                                                                                                              #
    #---------------------------------------------------------------------------------------------------------------------------------------------#

    if "s" in constraints:
        for index in range(L):
            m.add_constraint(m.sum(alpha[index][j] for j in range(D)) 
                            <= constraints["s"])                                        # Max lines per scoring system  

    for index in fairness_labels:                                                       # The fairness must be respected for each labels
        for g in fairness_groups:                                                       # The fairness must be respected for each group

            i_g = [i for i in range(N) if x[i][g] == 1]                                 # Get the in group samples indexes
            i_g_bar = [i for i in range(N) if x[i][g] == 0]                             # Get the not in group samples indexes
            N_g = len(i_g)
            N_g_bar = len(i_g_bar)

            i_g_pos = [i for i in range(N) if x[i][g] == 1 and y[i][index] == 1]
            i_g_neg = [i for i in range(N) if x[i][g] == 1 and y[i][index] == 0]
            N_g_pos = len(i_g_pos)
            N_g_neg = len(i_g_neg)

            i_g_bar_pos = [i for i in range(N) if x[i][g] == 0 and y[i][index] == 1]
            i_g_bar_neg = [i for i in range(N) if x[i][g] == 0 and y[i][index] == 0]
            N_g_bar_pos = len(i_g_bar_pos)
            N_g_bar_neg = len(i_g_bar_neg)

            if N_g == 0 or N_g_bar == 0:
                print("[WARNING] At least one of the protected groups is empty, skipping fairness constraints")
                break

            if "omr" in constraints:
                m.add_constraint(-constraints['omr'] 
                                <= (1/N_g)*(m.sum(pos[i][index] for i in i_g_neg) + m.sum(1 - pos[i][index] for i in i_g_pos)) - (1/N_g_bar)*(m.sum(pos[i][index] for i in i_g_bar_neg) + m.sum(1 - pos[i][index] for i in i_g_bar_pos)))
                m.add_constraint((1/N_g)*(m.sum(pos[i][index] for i in i_g_neg) + m.sum(1 - pos[i][index] for i in i_g_pos)) - (1/N_g_bar)*(m.sum(pos[i][index] for i in i_g_bar_neg) + m.sum(1 - pos[i][index] for i in i_g_bar_pos))
                                <= constraints['omr'])
                                
            if "sp" in constraints and i_g and i_g_bar:
                m.add_constraint(-constraints['sp'] 
                                <= (1/N_g)*m.sum(pos[i][index] for i in i_g) - (1/N_g_bar)*m.sum(pos[i][index] for i in i_g_bar))
                m.add_constraint((1/N_g)*m.sum(pos[i][index] for i in i_g) - (1/N_g_bar)*m.sum(pos[i][index] for i in i_g_bar)
                                <= constraints['sp'])

            if "pe" in constraints and i_g_neg and i_g_bar_neg:
                m.add_constraint(-constraints['pe'] 
                                <= (1/N_g_neg)*m.sum(pos[i][index] for i in i_g_neg) - (1/N_g_bar_neg)*m.sum(pos[i][index] for i in i_g_bar_neg))
                m.add_constraint((1/N_g_neg)*m.sum(pos[i][index] for i in i_g_neg) - (1/N_g_bar_neg)*m.sum(pos[i][index] for i in i_g_bar_neg)
                                <= constraints['pe'])

            if "eo" in constraints and i_g_pos and i_g_bar_pos:
                m.add_constraint(-constraints['eo'] 
                                <= (1/N_g_pos)*m.sum(pos[i][index] for i in i_g_pos) - (1/N_g_bar_pos)*m.sum(pos[i][index] for i in i_g_bar_pos))
                m.add_constraint((1/N_g_pos)*m.sum(pos[i][index] for i in i_g_pos) - (1/N_g_bar_pos)*m.sum(pos[i][index] for i in i_g_bar_pos)
                                <= constraints['eo'])     

            if "eod" in constraints and i_g_neg and i_g_bar_neg and i_g_pos and i_g_bar_pos:
                m.add_constraint(-constraints['eod'] 
                                <= (1/N_g_neg)*m.sum(pos[i][index] for i in i_g_neg) - (1/N_g_bar_neg)*m.sum(pos[i][index] for i in i_g_bar_neg))
                m.add_constraint((1/N_g_neg)*m.sum(pos[i][index] for i in i_g_neg) - (1/N_g_bar_neg)*m.sum(pos[i][index] for i in i_g_bar_neg)
                                <= constraints['eod']) 
                m.add_constraint(-constraints['eod'] 
                                <= (1/N_g_pos)*m.sum(pos[i][index] for i in i_g_pos) - (1/N_g_bar_pos)*m.sum(pos[i][index] for i in i_g_bar_pos))
                m.add_constraint((1/N_g_pos)*m.sum(pos[i][index] for i in i_g_pos) - (1/N_g_bar_pos)*m.sum(pos[i][index] for i in i_g_bar_pos)
                                <= constraints['eod']) 
                                

    #---------------------------------------------------------------------------------------------------------------------------------------------#
    #    OBJECTIVES                                                                                                                               #
    #---------------------------------------------------------------------------------------------------------------------------------------------#

    if "a" in objectives and not("s" in constraints):
        m.minimize((1/N)*m.sum(z[i] for i in range(N)))                                                     # Minimize loss

    if "ba" in objectives and not("s" in constraints):
        m.minimize(m.sum(m.sum(z[index] for index in indexes) / N_class[i] for i, indexes in enumerate(class_indexes)) / len(N_class))                                                     # Minimize loss


    if "a" in objectives and "s" in constraints:
        m.minimize((1/N)*m.sum(z[i] for i in range(N))                                                      # Minimize loss
            + (1/(constraints["s"]*L*N))*m.sum(alpha[l][j] for l in range(L) for j in range(D)))            # Minimize alphas

    if "ba" in objectives and "s" in constraints:
        m.minimize(m.sum(m.sum(z[index] for index in indexes) / N_class[i] for i, indexes in enumerate(class_indexes)) / len(N_class)   # Minimize balanced loss
            + (1/(constraints["s"]*L*N))*m.sum(alpha[l][j] for l in range(L) for j in range(D)))            # Minimize alphas
                                                                                                        

    #---------------------------------------------------------------------------------------------------------------------------------------------#
    #    SOLVE AND RETURN                                                                                                                         #
    #---------------------------------------------------------------------------------------------------------------------------------------------#

    sol = m.solve(log_output=show_progress)                                             # Solve the model and get the lambda coefficients
    execution_time = m.solve_details.time                                               # Keep track of th execution time
    gap = m.solve_details.gap
    objective = sol.get_objective_value()
    l_lists = []

    if sol:
        for i in range(L):
            l_list = []
            for s in sol.get_values(l[i]):                                              # Get lambda coefficients
                l_list.append(np.rint(s))
            l_lists.append(l_list)                                                       
    else:
        print("[ERROR] Found no solution for this configuration, you may want to soften your constraints")
    
    return l_lists, execution_time, gap, objective