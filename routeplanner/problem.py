import numbers
from dataclasses import dataclass
import numpy as np
from routeplanner.typechecker import check_number, check_onedim_ndarray_of_numbers, check_collection_of_numbers

class IndividualProblemGenerator:
    # For more details see section 3.2 of report
    def __init__(self, x_mean: numbers.Real, x_half_interval: numbers.Real, y_mean: numbers.Real, y_half_interval: numbers.Real, 
                 wind_speed_mean: numbers.Real,  wind_speed_half_interval: numbers.Real, 
                 UAV_speed_coef: numbers.Real, UAV_flight_time_limit_coef: numbers.Real,
                 random_state: numbers.Integral):
        check_number(x_mean, "x_mean", numbers.Real)
        self.__x_mean = x_mean
        check_number(x_half_interval, "x_half_interval", numbers.Real, sign_check="non_neg")
        self.__x_half_interval = x_half_interval
        check_number(y_mean, "y_mean", numbers.Real)
        self.__y_mean = y_mean
        check_number(y_half_interval, "y_half_interval", numbers.Real, sign_check="non_neg")
        self.__y_half_interval = y_half_interval

        check_number(wind_speed_mean, "wind_speed_mean", numbers.Real, sign_check="non_neg")
        self.__wind_speed_mean = wind_speed_mean
        check_number(wind_speed_half_interval, "wind_speed_half_interval", numbers.Real, sign_check="non_neg")
        self.__wind_speed_half_interval = wind_speed_half_interval

        check_number(UAV_speed_coef, "UAV_speed_coef", numbers.Real, sign_check="pos")
        self.__UAV_speed_coef = UAV_speed_coef
        check_number(UAV_flight_time_limit_coef, "UAV_flight_time_limit_coef", numbers.Real, sign_check="pos")
        self.__UAV_flight_time_limit_coef = UAV_flight_time_limit_coef

        check_number(random_state, "random_state", numbers.Integral)
        self.__rng = np.random.default_rng(random_state)

    def generate(self, n_objects: numbers.Integral):
        check_number(n_objects, "n_objects", numbers.Integral, sign_check="non_neg")

        x_coords = self.__rng.uniform(
            low=self.__x_mean-self.__x_half_interval, 
            high=self.__x_mean+self.__x_half_interval, 
            size=n_objects+2
        )
        y_coords = self.__rng.uniform(
            low=self.__y_mean-self.__y_half_interval, 
            high=self.__y_mean+self.__y_half_interval,
            size=n_objects+2
        )

        wind_speed = self.__rng.uniform(
            low=self.__wind_speed_mean-self.__wind_speed_half_interval, 
            high=self.__wind_speed_mean+self.__wind_speed_half_interval,
            size=1
        )[0]
        wind_angle = self.__rng.uniform(low=0, high=2*np.pi, size=1)[0]
        wind_vector = (wind_speed*np.cos(wind_angle), wind_speed*np.sin(wind_angle))

        UAV_speed = self.__UAV_speed_coef*wind_speed
        UAV_flight_time_limit = (self.__UAV_flight_time_limit_coef * 
                                 4*self.__x_half_interval*self.__y_half_interval * n_objects)

        return UAVPathPlanningProblem(
            x_coords = x_coords,
            y_coords = y_coords,
            UAV_speed = UAV_speed,
            UAV_flight_time_limit = UAV_flight_time_limit,
            wind_vector = wind_vector
        )
    def generate_list(self, n_objects: numbers.Integral, n_problems: numbers.Integral):
        check_number(n_problems, "n_problems", numbers.Integral, sign_check="non_neg")
        return [self.generate(n_objects) for i in range(n_problems)]

@dataclass(frozen=True)
class UAVPathPlanningProblem:
    x_coords: np.ndarray[np.number]
    y_coords: np.ndarray[np.number]
    UAV_speed: numbers.Real
    UAV_flight_time_limit: numbers.Real
    wind_vector: tuple[numbers.Real]

    def __post_init__(self):        
        check_onedim_ndarray_of_numbers(self.x_coords, "x_coords", np.number, min_vals_count=2)
        check_onedim_ndarray_of_numbers(self.y_coords, "y_coords", np.number, min_vals_count=2)
        if len(self.x_coords) != len(self.y_coords):
            raise ValueError("x_coords and y_coords must have equal number of elements")
        
        check_number(self.UAV_speed, "UAV_speed", numbers.Real, sign_check="pos")
        check_number(self.UAV_flight_time_limit, "UAV_flight_time_limit", numbers.Real, sign_check="pos")
        
        check_collection_of_numbers(self.wind_vector, "wind_vector", tuple, numbers.Real)
        if len(self.wind_vector) != 2:
            raise ValueError("wind_vector must have equally 2 values")
    
    @property
    def n_objects(self):
        return len(self.x_coords)-2
    @property
    def takeoff_point(self):
        return (self.x_coords[0], self.y_coords[0])
    @property
    def landing_point(self):
        return (self.x_coords[-1], self.y_coords[-1])