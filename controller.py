import json
from tkinter import ttk, filedialog
from routeplanner.problem import IndividualProblemGenerator
from routeplanner.solvers import greedy, ACO

class Controller:
    def load_file(self, path):
        if path:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        return None
    def get_generated_problem(problem_data: dict, random_state: int):
        n_objects = problem_data["n_objects"]
        del problem_data["n_objects"]
        pg = IndividualProblemGenerator(**{**problem_data, "random_state": random_state})
        problem = pg.generate(n_objects)
        

    # def run(self, alg, coords, params):
        # if alg == "greedy":
        #     path, length = greedy_solver(coords)
        #     return {
        #         "path": path,
        #         "length": length,
        #         "history": None
        #     }

        # else:
        #     path, length, history = aco_solver(coords, params)
        #     return {
        #         "path": path,
        #         "length": length,
        #         "history": history
        #     }