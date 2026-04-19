import os
import json
import numpy as np
from routeplanner.problem import IndividualProblemGenerator, UAVPathPlanningProblem
from routeplanner.solvers import greedy, ACO, iter_num_func
from routeplanner.experiments import test_termination_condition, test_specific_param, test_time_and_accuracy

class Controller:
    __N_JOBS = max(os.cpu_count() - 2, 1)

    def load_file(self, path):
        if path:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        return None
    
    def save_file(self, path, problem_data: dict):
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(problem_data, f, indent=4)

    def get_generated_problem(self, problem_generator_params: dict, random_state: int):
        n_objects = problem_generator_params["n_objects"]
        del problem_generator_params["n_objects"]
        pg = IndividualProblemGenerator(**{**problem_generator_params, "random_state": random_state})
        problem = pg.generate(n_objects)
        return problem.to_dict()
        
    def run_greedy(self, problem_data: dict):
        problem = UAVPathPlanningProblem(**problem_data)
        return greedy(problem)
    
    def run_ACO(self, problem_data: dict, ACO_params:dict, random_state):
        problem = UAVPathPlanningProblem(**problem_data)
        n_iners_unchanged = iter_num_func(ACO_params["iter_num_func_coef"], ACO_params["n_ants_in_pop"], problem.n_objects)
        del ACO_params["iter_num_func_coef"]
        return ACO(**{
            "problem": problem, 
            **ACO_params, 
            "n_iters_without_improvement": n_iners_unchanged, 
            "random_state": random_state, 
            "save_solution_dynamic": True
        })
    
    def run_termination_condition_experiment(self, problem_sizes_range: dict, fixed_problem_generator_params: dict,
                                             iter_num_func_coefs_range: dict, fixed_ACO_params:dict, n_exps, random_state):
        problem_sizes = np.arange(
            problem_sizes_range["from"], 
            problem_sizes_range["to"]+problem_sizes_range["step"]/2, 
            problem_sizes_range["step"], dtype=np.int64
        ).tolist()
        iter_num_func_coefs = np.arange(
            iter_num_func_coefs_range["from"], 
            iter_num_func_coefs_range["to"]+iter_num_func_coefs_range["step"]/2, 
            iter_num_func_coefs_range["step"]
        ).tolist()
        pg = IndividualProblemGenerator(**{**fixed_problem_generator_params, "random_state": random_state})
        return test_termination_condition(**{
            "problem_generator": pg,
            **fixed_ACO_params,
            "iter_num_func": iter_num_func, 
            "alg_random_state": random_state, 
            "iter_num_func_coefs": iter_num_func_coefs, 
            "problem_sizes": problem_sizes, 
            "n_exps": n_exps,
            "n_jobs": self.__N_JOBS
        })

    def run_specific_parameter_experiment(self, problem_sizes_range: dict, fixed_problem_generator_params: dict, 
                                          alphas_range: dict, fixed_ACO_params:dict, n_exps, random_state):
        problem_sizes = np.arange(
            problem_sizes_range["from"], 
            problem_sizes_range["to"]+problem_sizes_range["step"]/2, 
            problem_sizes_range["step"], dtype=np.int64
        ).tolist()
        alphas = np.arange(
            alphas_range["from"], 
            alphas_range["to"]+alphas_range["step"]/2, 
            alphas_range["step"]
        ).tolist()
        pg = IndividualProblemGenerator(**{**fixed_problem_generator_params, "random_state": random_state})
        return test_specific_param(**{
            "problem_generator": pg, 
            **fixed_ACO_params,
            "iter_num_func": iter_num_func, 
            "alg_random_state": random_state, 
            "alphas": alphas,
            "problem_sizes": problem_sizes, 
            "n_exps": n_exps,
            "n_jobs": self.__N_JOBS
        })
    
    def run_time_and_accuracy_experiment(self, problem_sizes_range: dict, fixed_problem_generator_params: dict, 
                                         fixed_ACO_params:dict, n_exps, random_state):
        problem_sizes = np.arange(
            problem_sizes_range["from"], 
            problem_sizes_range["to"]+problem_sizes_range["step"]/2, 
            problem_sizes_range["step"], dtype=np.int64
        ).tolist()
        pg = IndividualProblemGenerator(**{**fixed_problem_generator_params, "random_state": random_state})
        return test_time_and_accuracy(**{
            "problem_generator": pg, 
            **fixed_ACO_params,
            "iter_num_func": iter_num_func, 
            "alg_random_state": random_state, 
            "problem_sizes": problem_sizes, 
            "n_exps": n_exps,
            "n_jobs": self.__N_JOBS
        })
