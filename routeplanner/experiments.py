import numbers
import numpy as np
import pandas as pd
from routeplanner.typechecker import check_number, check_collection_of_numbers
from routeplanner.problem import IndividualProblemGenerator
from routeplanner.solvers import greedy, ACO
from multiprocessing import Pool

def test_termination_condition(problem_generator: IndividualProblemGenerator,                 
                               alpha: numbers.Real, beta: numbers.Real, ro: numbers.Real, initial_pheromone_level: numbers.Real, 
                               n_ants_in_pop: numbers.Integral, iter_num_func, alg_random_state: numbers.Integral,
                               iter_num_func_coefs: list[numbers.Real], problem_sizes: list[numbers.Integral], n_exps: numbers.Integral, n_jobs: int = None):
    if not isinstance(problem_generator, IndividualProblemGenerator):
        raise TypeError("problem_generator must be IndividualProblemGenerator")
    check_number(alg_random_state, "alg_random_state", numbers.Integral)
    check_number(n_exps, "n_exps", numbers.Integral, sign_check="pos")
    check_collection_of_numbers(iter_num_func_coefs, "iter_num_func_coefs", list, numbers.Real, 
                                min_vals_count=1, sign_check="pos")
    check_collection_of_numbers(problem_sizes, "problem_sizes", list, numbers.Integral,
                                min_vals_count=1, sign_check="pos")

    rng = np.random.default_rng(alg_random_state)
    raw_stats: list[list[numbers.Real]] = []

    with Pool(n_jobs) as pool:
        for coef in iter_num_func_coefs:
            for problem_size in problem_sizes:
                args = list(zip(
                    problem_generator.generate_list(problem_size, n_exps),
                    [alpha]*n_exps,
                    [beta]*n_exps,
                    [ro]*n_exps,
                    [initial_pheromone_level]*n_exps,
                    [n_ants_in_pop]*n_exps,
                    [iter_num_func(coef, n_ants_in_pop, problem_size)]*n_exps,
                    rng.integers(0, 1_000_000, n_exps).tolist()
                ))
                exp_results = list(pool.starmap(ACO, args))
                for res in exp_results:
                    raw_stats.append([coef, problem_size, res.objects_inspected])
    
    return pd.DataFrame(columns=["iter_num_func_coef", "problem_size", "objective_function"], data=raw_stats)

def test_specific_param(problem_generator: IndividualProblemGenerator,
                        beta: numbers.Real, ro: numbers.Real, initial_pheromone_level: numbers.Real, n_ants_in_pop: numbers.Integral, 
                        iter_num_func, iter_num_func_coef: numbers.Real, alg_random_state: numbers.Integral,
                        alphas: list[numbers.Real], problem_sizes: list[numbers.Integral], n_exps: numbers.Integral, n_jobs: int = None):
    if not isinstance(problem_generator, IndividualProblemGenerator):
        raise TypeError("problem_generator must be IndividualProblemGenerator")
    check_number(alg_random_state, "alg_random_state", numbers.Integral)
    check_number(iter_num_func_coef, "iter_num_func_coef", numbers.Real, sign_check="pos")
    check_number(n_exps, "n_exps", numbers.Integral, sign_check="pos")
    check_collection_of_numbers(alphas, "alphas", list, numbers.Real, 
                                min_vals_count=1)
    check_collection_of_numbers(problem_sizes, "problem_sizes", list, numbers.Integral,
                                min_vals_count=1, sign_check="pos")
    
    rng = np.random.default_rng(alg_random_state)
    raw_stats: list[list[numbers.Real]] = []
    with Pool(n_jobs) as pool:
        for alpha in alphas:
            for problem_size in problem_sizes:
                args = list(zip(
                    problem_generator.generate_list(problem_size, n_exps),
                    [alpha]*n_exps,
                    [beta]*n_exps,
                    [ro]*n_exps,
                    [initial_pheromone_level]*n_exps,
                    [n_ants_in_pop]*n_exps,
                    [iter_num_func(iter_num_func_coef, n_ants_in_pop, problem_size)]*n_exps,
                    rng.integers(0, 1_000_000, n_exps).tolist()
                ))
                exp_results = list(pool.starmap(ACO, args))
                for res in exp_results:
                    raw_stats.append([alpha, problem_size, res.objects_inspected])
    
    return pd.DataFrame(columns=["alpha", "problem_size", "objective_function"], data=raw_stats)

def test_time_and_accuracy(problem_generator: IndividualProblemGenerator,
                           alpha: numbers.Real, beta: numbers.Real, ro: numbers.Real, initial_pheromone_level: numbers.Real, n_ants_in_pop: numbers.Integral, 
                           iter_num_func, iter_num_func_coef: numbers.Real, alg_random_state: numbers.Integral,
                           problem_sizes: list[numbers.Integral], n_exps: numbers.Integral, n_jobs: int = None):
    if not isinstance(problem_generator, IndividualProblemGenerator):
        raise TypeError("problem_generator must be IndividualProblemGenerator")
    check_number(alg_random_state, "alg_random_state", numbers.Integral)
    check_number(iter_num_func_coef, "iter_num_func_coef", numbers.Real, sign_check="pos")
    check_number(n_exps, "n_exps", numbers.Integral, sign_check="pos")
    check_collection_of_numbers(problem_sizes, "problem_sizes", list, numbers.Integral,
                                min_vals_count=1, sign_check="pos")
    
    rng = np.random.default_rng(alg_random_state)
    raw_stats: list[list[numbers.Real]] = []
    with Pool(n_jobs) as pool:
        for problem_size in problem_sizes:
            ind_problems = problem_generator.generate_list(problem_size, n_exps)
            greedy_exp_results = list(pool.map(greedy, ind_problems))

            ACO_args = list(zip(
                    ind_problems,
                    [alpha]*n_exps,
                    [beta]*n_exps,
                    [ro]*n_exps,
                    [initial_pheromone_level]*n_exps,
                    [n_ants_in_pop]*n_exps,
                    [iter_num_func(iter_num_func_coef, n_ants_in_pop, problem_size)]*n_exps,
                    rng.integers(0, 1_000_000, n_exps).tolist()
                ))
            ACO_exp_results = list(pool.starmap(ACO, ACO_args))

            for i in range(n_exps):                
                greedy_objective_function = greedy_exp_results[i].objects_inspected
                ACO_objective_function = ACO_exp_results[i].objects_inspected
                raw_stats.append([problem_size, greedy_objective_function, greedy_exp_results[i].solving_time_sec,
                                  ACO_objective_function, ACO_exp_results[i].solving_time_sec, 
                                  delta(greedy_objective_function, ACO_objective_function)])

    return pd.DataFrame(columns=["problem_size", "greedy_objective_function", "greedy_solving_time_sec", 
                                 "ACO_objective_function", "ACO_solving_time_sec", 
                                 "delta"], data=raw_stats)

def delta(greedy_objective_function, ACO_objective_function):
    return (ACO_objective_function - greedy_objective_function) / greedy_objective_function