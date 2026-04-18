import numbers
from dataclasses import dataclass
import time
import numpy as np
from routeplanner.typechecker import  check_number, check_collection_of_numbers
from routeplanner.problem import UAVPathPlanningProblem

def greedy(problem: UAVPathPlanningProblem):
    time_start = time.perf_counter()
    time_matrix = calc_time_matrix(problem)

    all_node_indices = np.arange(problem.n_objects+2)
    nodes_mask = __clean_nodes_mask(problem.n_objects)
    allowed_nodes_indices = __allowed_nodes_indices(all_node_indices, nodes_mask, 0,
                                                    time_matrix, 0, problem.UAV_flight_time_limit)
    route = None
    if not len(allowed_nodes_indices):
        if time_matrix[0, problem.n_objects+1] <= problem.UAV_flight_time_limit:
            route = [np.int64(0), np.int64(problem.n_objects+1)]
        return UAVPathPlanningProblemSolution(
            route=route,
            objects_inspected=0,
            solving_time_sec=time.perf_counter()-time_start,
            iter_best_objects_inspected_dynamic=None,
            record_best_objects_inspected_dynamic=None
        )
    
    route = [np.int64(0)]
    total_time = 0
    while len(allowed_nodes_indices):
        next_node = allowed_nodes_indices[np.argmin(time_matrix[route[-1], allowed_nodes_indices])]        
        total_time += time_matrix[route[-1], next_node]
        nodes_mask[next_node] = True
        route.append(next_node)

        allowed_nodes_indices = __allowed_nodes_indices(all_node_indices, nodes_mask, route[-1], 
                                                        time_matrix, total_time, problem.UAV_flight_time_limit)
    route.append(np.int64(problem.n_objects+1))

    return UAVPathPlanningProblemSolution(
        route=route,
        objects_inspected=len(route)-2,
        solving_time_sec=time.perf_counter()-time_start,
        iter_best_objects_inspected_dynamic=None,
        record_best_objects_inspected_dynamic=None
    )

def ACO(problem: UAVPathPlanningProblem, 
        alpha: numbers.Real, beta: numbers.Real, ro: numbers.Real, initial_pheromone_level: numbers.Real, 
        n_ants_in_pop: numbers.Integral, n_iters_without_improvement: numbers.Integral, 
        random_state, save_solution_dynamic=False):
    check_number(alpha, "alpha", numbers.Real, sign_check="non_neg")
    check_number(beta, "beta", numbers.Real, sign_check="non_neg")
    check_number(ro, "ro", numbers.Real, sign_check="non_neg")
    check_number(initial_pheromone_level, "initial_pheromone_level", numbers.Real, sign_check="pos")
    check_number(n_ants_in_pop, "n_ants_in_pop", numbers.Integral, sign_check="pos")
    check_number(n_iters_without_improvement, "n_iters_without_improvement", numbers.Integral, sign_check="pos")
    check_number(random_state, "random_state", numbers.Integral)

    rng = np.random.default_rng(random_state)

    time_start = time.perf_counter()
    all_node_indices = np.arange(problem.n_objects+2)
    time_matrix = calc_time_matrix(problem)
    pheromone_matrix = (np.ones((problem.n_objects+2, problem.n_objects+2), dtype=np.float64)*
                        initial_pheromone_level)
    best_solution = None
    best_objects_inspected = 0
        
    iter_best_objects_inspected_dynamic = [] if save_solution_dynamic else None
    record_best_objects_inspected_dynamic = [] if save_solution_dynamic else None

    # Problem solution existance check
    nodes_mask = __clean_nodes_mask(problem.n_objects)
    allowed_at_start = __allowed_nodes_indices(all_node_indices, nodes_mask, 0, 
                          time_matrix, 0, problem.UAV_flight_time_limit)
    if not len(allowed_at_start):
        if time_matrix[0, problem.n_objects+1] <= problem.UAV_flight_time_limit:
            best_solution = [0, problem.n_objects+1]
        return UAVPathPlanningProblemSolution(
            route=best_solution,
            objects_inspected=best_objects_inspected,
            solving_time_sec=time.perf_counter()-time_start,
            iter_best_objects_inspected_dynamic=iter_best_objects_inspected_dynamic,
            record_best_objects_inspected_dynamic=record_best_objects_inspected_dynamic
        )
    
    iters_unchanged = 0
    while iters_unchanged < n_iters_without_improvement:
        iter_best_objects_inspected = 0        
        pheromone_increment_matrix = np.zeros((problem.n_objects+2, problem.n_objects+2))

        for k in range(n_ants_in_pop):
            ant_route_time = 0
            ant_route = [np.int64(0)] # This list contains indices of nodes visited by the current ant
            ant_visited_nodes_mask = __clean_nodes_mask(problem.n_objects)
            ant_allowed_nodes_indices = __allowed_nodes_indices(all_node_indices, ant_visited_nodes_mask, ant_route[-1], 
                                                                time_matrix, ant_route_time, problem.UAV_flight_time_limit)
            while len(ant_allowed_nodes_indices):
                # Formulae 2.3 in report
                objects_prob_coefs = (np.pow(pheromone_matrix[ant_route[-1], ant_allowed_nodes_indices], alpha)*
                                      np.pow(time_matrix[ant_route[-1], ant_allowed_nodes_indices], -beta))
                objects_probs = objects_prob_coefs / objects_prob_coefs.sum()
                # print("objects_probs", objects_probs)
                next_object = rng.choice(a=ant_allowed_nodes_indices, p=objects_probs)

                ant_route_time += time_matrix[ant_route[-1], next_object]
                ant_route.append(next_object)
                ant_visited_nodes_mask[next_object] = True
                ant_allowed_nodes_indices = __allowed_nodes_indices(all_node_indices, ant_visited_nodes_mask, ant_route[-1],
                                                                    time_matrix, ant_route_time, problem.UAV_flight_time_limit)
            ant_route.append(np.int64(problem.n_objects+1))
            ant_route_objects_count = len(ant_route)-2
            
            iters_unchanged += 1
            if ant_route_objects_count > best_objects_inspected:
                best_objects_inspected = ant_route_objects_count
                best_solution = ant_route
                iters_unchanged = 0
            
            if save_solution_dynamic and ant_route_objects_count > iter_best_objects_inspected:
                iter_best_objects_inspected = ant_route_objects_count
            
            # Formulae 2.4 in report
            ant_pheromone_increment = ant_route_objects_count / problem.n_objects
            np.add.at(pheromone_increment_matrix, (ant_route[:-1], ant_route[1:]), ant_pheromone_increment)

        pheromone_matrix = (1 - ro) * pheromone_matrix + pheromone_increment_matrix

        if save_solution_dynamic:
            iter_best_objects_inspected_dynamic.append(iter_best_objects_inspected)
            record_best_objects_inspected_dynamic.append(best_objects_inspected)
    
    return UAVPathPlanningProblemSolution(
        route=best_solution,
        objects_inspected=best_objects_inspected,
        solving_time_sec=time.perf_counter()-time_start,
        iter_best_objects_inspected_dynamic=iter_best_objects_inspected_dynamic,
        record_best_objects_inspected_dynamic=record_best_objects_inspected_dynamic
    )

def __allowed_nodes_indices(all_node_indices, visited_nodes_mask, current_node_index, 
                            time_matrix, current_flight_time, flight_time_limit):
    # See 2.2 in report
    unvisited_objects_ind = all_node_indices[~visited_nodes_mask]
    time_from_current_to_unvisited_node = time_matrix[current_node_index, unvisited_objects_ind]
    time_from_unvisited_to_landing_node = time_matrix[unvisited_objects_ind, len(all_node_indices)-1].ravel()
    flight_times = current_flight_time+time_from_current_to_unvisited_node+time_from_unvisited_to_landing_node
    return unvisited_objects_ind[flight_times <= flight_time_limit]

def __clean_nodes_mask(n_objects):
    nodes_mask = np.zeros(n_objects+2, dtype=bool)
    nodes_mask[[0, n_objects+1]] = True # To exclude takeoff and landing nodes
    return nodes_mask

def calc_time_matrix(problem: UAVPathPlanningProblem) -> np.ndarray:
    if not isinstance(problem, UAVPathPlanningProblem):
        raise TypeError("problem must be UAVPathPlanningProblem")
    # Formulae 1.2 implementation
    x_coords_difs = -problem.x_coords[:, None] + problem.x_coords
    y_coords_difs = -problem.y_coords[:, None] + problem.y_coords    
    arc_lengths = np.sqrt(np.pow(x_coords_difs, 2) + np.pow(y_coords_difs, 2))
    np.fill_diagonal(arc_lengths, np.nan)
    unit_vecs_x_coords = x_coords_difs / arc_lengths
    unit_vecs_y_coords = y_coords_difs / arc_lengths
    # Common value of 2 roots in formulae 1.10
    root_common_part = (unit_vecs_x_coords*problem.wind_vector[0] + 
                        unit_vecs_y_coords*problem.wind_vector[1])
    # THe value under the root in formulae 1.10
    under_sqrt_part = (np.pow(problem.UAV_speed, 2) - 
                       np.pow(unit_vecs_y_coords*problem.wind_vector[0]-
                              unit_vecs_x_coords*problem.wind_vector[1], 2))
    under_sqrt_part[under_sqrt_part<0] = np.nan
    under_sqrt_part = np.sqrt(under_sqrt_part)

    roots_1 = root_common_part + under_sqrt_part
    roots_1[roots_1<=0] = np.nan
    roots_2 = root_common_part - under_sqrt_part
    roots_2[roots_2<=0] = np.nan
    real_UAV_speed = np.fmax(roots_1, roots_2)
    # Formulae 1.11
    real_UAV_time = arc_lengths / real_UAV_speed
    return real_UAV_time

@dataclass(frozen=True)
class UAVPathPlanningProblemSolution:
    route: list[numbers.Integral]
    objects_inspected: numbers.Integral
    solving_time_sec: numbers.Real
    iter_best_objects_inspected_dynamic: list[numbers.Integral]
    record_best_objects_inspected_dynamic: list[numbers.Integral]
    
    def __post_init__(self):
        check_collection_of_numbers(self.route, "route", list, numbers.Integral)
        check_number(self.objects_inspected, "objects_inspected", numbers.Integral, sign_check="non_neg")
        check_number(self.solving_time_sec, "solving_time_sec", numbers.Real, sign_check="non_neg")
        if self.iter_best_objects_inspected_dynamic:
            check_collection_of_numbers(self.iter_best_objects_inspected_dynamic, "iter_best_objects_inspected_dynamic", 
                                        list, numbers.Integral)
        if self.record_best_objects_inspected_dynamic:
            check_collection_of_numbers(self.record_best_objects_inspected_dynamic, "record_best_objects_inspected_dynamic", 
                                        list, numbers.Integral)
