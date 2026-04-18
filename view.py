import json
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
import random
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from routeplanner.problem import UAVPathPlanningProblem
from controller import Controller


class AppView:
    __SEED_UI_NAME = "Зерно ГПВЧ"

    __PROBLEM_DATA_SYS_NAMES = ["x_coords", "y_coords", "UAV_speed", "UAV_flight_time_limit", "wind_vector"]
    __PROBLEM_DATA_UI_NAMES = ["x", "y", "v", "T", "w"]

    __PROBLEM_GEN_PARAMS_SYS_NAMES = ["x_mean", "x_half_interval", "y_mean", "y_half_interval", 
                                      "wind_speed_mean", "wind_speed_half_interval", "UAV_speed_coef", "UAV_flight_time_limit_coef", "n_objects"]
    __PROBLEM_GEN_PARAMS_UI_NAMES = ["x\u0305", "∆x", "y\u0305", "∆y",
                                     "|w\u0305|", "∆w", "rv", "rT", "n"]

    __ACO_PARAMS_SYS_NAMES = ["alpha", "beta", "ro", "initial_pheromone_level", "n_ants_in_pop", "iter_num_func_coef"]
    __ACO_PARAMS_UI_NAMES = ["α", "β", "ρ", "τ\u2080", "μ", "η"]

    __SIGN_CHECK_MODES = [None, "neg", "non_neg", "non_pos", "pos"]

    def __init__(self, root: tk.Tk, controller: Controller):
        if not isinstance(root, tk.Tk):
            raise TypeError("root must be Tk")
        if not isinstance(controller, Controller):
            raise TypeError("controller must be Controller")
        self.root = root
        self.controller = controller

        self.root.title("Задача скадання маршруту БПЛА")
        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True)

        self.ind_prob_work_tab = ttk.Frame(notebook)
        self.tab2 = ttk.Frame(notebook)
        self.tab3 = ttk.Frame(notebook)
        self.tab4 = ttk.Frame(notebook)

        notebook.add(self.ind_prob_work_tab, text="Робота з ІЗ")
        notebook.add(self.tab2, text="Tab2")
        notebook.add(self.tab3, text="Tab3")
        notebook.add(self.tab4, text="Tab4")

        style = ttk.Style()
        self.font_size = 12
        self.font = "Aerial"
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=self.font_size)
        style.configure(".", font=(self.font, self.font_size))
        style.configure("My.TFrame", borderwidth=1, relief="solid")

        self.build_ind_prob_work_tab()

    def build_ind_prob_work_tab(self):
        frame = self.ind_prob_work_tab
        settings_frame = ttk.Frame(frame, style="My.TFrame")
        settings_frame.grid(row=0, column=0)
        graph_frame = ttk.Frame(frame)
        graph_frame.grid(row=0, column=1)
        log_frame = ttk.Frame(frame)
        log_frame.grid(row=0, column=2)

        input_check_frame = ttk.Frame(settings_frame)
        input_check_frame.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        ttk.Label(input_check_frame, text="Спосіб введення даних ІЗ:", 
                  font=(self.font, self.font_size, "bold")).grid(row=0, column=0, sticky="w")
        self.input_mode = tk.StringVar(value="manual")
        ttk.Radiobutton(input_check_frame, text="Ввести вручну", variable=self.input_mode, value="manual",
                        command=self.__update_additional_input).grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(input_check_frame, text="Згенерувати", variable=self.input_mode, value="generate",
                        command=self.__update_additional_input).grid(row=2, column=0, sticky="w")
        ttk.Radiobutton(input_check_frame, text="Зчитати з файлу", variable=self.input_mode, value="file",
                        command=self.__update_additional_input).grid(row=3, column=0, sticky="w")

        self.prob_input_frame = ttk.Frame(input_check_frame, style="My.TFrame", borderwidth=1)
        self.prob_input_frame.grid(row=4, column=0, pady=10, sticky="we")
        self.prob_input_frame.columnconfigure(0, weight=1)
        self.prob_input_frame.columnconfigure(1, weight=1)
        ttk.Label(self.prob_input_frame, text="Вхідні дані ІЗ за мат. моделлю",
                  font=(self.font, self.font_size, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        self.problem_data_entries = {}
        self.problem_data_vars = {}
        for i, p_sys, p_ui in zip(range(len(self.__PROBLEM_DATA_SYS_NAMES)), 
                                  self.__PROBLEM_DATA_SYS_NAMES, self.__PROBLEM_DATA_UI_NAMES):
            ttk.Label(self.prob_input_frame, text=p_ui).grid(row=i+1, column=0, sticky="e")
            var = tk.StringVar()
            e = ttk.Entry(self.prob_input_frame, textvariable=var)
            e.grid(row=i+1, column=1, padx=10, sticky="e")
            self.problem_data_entries[p_sys] = e
            self.problem_data_vars[p_sys] = var


        self.prob_gen_params_frame = ttk.Frame(input_check_frame, style="My.TFrame", borderwidth=1)
        self.prob_gen_params_frame.columnconfigure(0, weight=1)
        self.prob_gen_params_frame.columnconfigure(1, weight=1)
        ttk.Label(self.prob_gen_params_frame, text="Параметри генератора ІЗ         ",
                  font=(self.font, self.font_size, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        self.problem_gen_params_entries = {}
        self.problem_gen_params_vars = {}
        for i, p_sys, p_ui in zip(range(len(self.__PROBLEM_GEN_PARAMS_SYS_NAMES)), 
                               self.__PROBLEM_GEN_PARAMS_SYS_NAMES, self.__PROBLEM_GEN_PARAMS_UI_NAMES):
            ttk.Label(self.prob_gen_params_frame, text=p_ui).grid(row=i+1, column=0, sticky="e")
            var = tk.StringVar()
            e = ttk.Entry(self.prob_gen_params_frame, textvariable=var)
            e.grid(row=i+1, column=1, padx=10, sticky="e")
            self.problem_gen_params_entries[p_sys] = e
            self.problem_gen_params_vars[p_sys] = var

        self.load_file_btn = ttk.Button(input_check_frame, text="Вибрати файл", command=self.controller.load_file)


        self.alg_check_frame = ttk.Frame(settings_frame)
        self.alg_check_frame.grid(row=2, column=0, padx=20, pady=10, sticky="w")
        ttk.Label(self.alg_check_frame, text="Алгоритм:", 
                  font=(self.font, self.font_size, "bold")).grid(row=0, column=0, sticky="w")
        self.alg = tk.StringVar(value="greedy")
        ttk.Radiobutton(self.alg_check_frame, text="ЖА", variable=self.alg, value="greedy", 
                        command=self.__update_ACO_params_frame).grid(row=1, column=0, sticky="w")
        ttk.Radiobutton(self.alg_check_frame, text="ACO", variable=self.alg, value="ACO", 
                        command=self.__update_ACO_params_frame).grid(row=2, column=0, sticky="w")
        
        seed_frame = ttk.Frame(settings_frame)
        seed_frame.grid(row=3, column=0, padx=20, pady=10, sticky="we")
        ttk.Label(seed_frame, text=self.__SEED_UI_NAME).grid(row=0, column=0, sticky="e")
        self.random_state = tk.StringVar()
        e = ttk.Entry(seed_frame, textvariable=self.random_state)
        e.grid(row=0, column=1, padx=10, sticky="e")

        

        self.ACO_params_frame = ttk.Frame(settings_frame, style="My.TFrame", borderwidth=1)
        self.ACO_params_frame.columnconfigure(0, weight=1)
        self.ACO_params_frame.columnconfigure(1, weight=1)
        ttk.Label(self.ACO_params_frame, text="Параметри алгоритму ACO",
                  font=(self.font, self.font_size, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")      
        self.ACO_params_entries = {}
        self.ACO_params_vars = {}
        for i, p_sys, p_ui in zip(range(len(self.__ACO_PARAMS_SYS_NAMES)), 
                               self.__ACO_PARAMS_SYS_NAMES, self.__ACO_PARAMS_UI_NAMES):
            ttk.Label(self.ACO_params_frame, text=p_ui).grid(row=i+1, column=0, sticky="e")
            var = tk.StringVar()
            e = ttk.Entry(self.ACO_params_frame, textvariable=var)
            e.grid(row=i+1, column=1, padx=10, sticky="e")
            self.ACO_params_entries[p_sys] = e
            self.ACO_params_vars[p_sys] = var

        ttk.Button(settings_frame, text="Розв'язати", command=self.run_individual_problem_solving).grid(row=5, column=0)


        # self.result_label = ttk.Label(frame, text="")
        # self.result_label.pack()

        # self.fig, self.ax = plt.subplots(figsize=(5,4))
        # self.canvas = FigureCanvasTkAgg(self.fig, master=frame)
        # self.canvas.get_tk_widget().pack()

        # self.fig2, self.ax2 = plt.subplots(figsize=(5,2))
        # self.canvas2 = FigureCanvasTkAgg(self.fig2, master=frame)
        # self.canvas2.get_tk_widget().pack()

    def __update_additional_input(self):
        if self.input_mode.get() == "manual":
            self.prob_input_frame.grid(row=4, column=0, pady=10, sticky="we")
        else:
            self.prob_input_frame.grid_remove()

        if self.input_mode.get() == "file":
            self.load_file_btn.grid(row=4, column=0)
        else:
            self.load_file_btn.grid_remove()

        if self.input_mode.get() == "generate":
            self.prob_gen_params_frame.grid(row=4, column=0, pady=10, sticky="we")
        else:
            self.prob_gen_params_frame.grid_remove()

    def __update_ACO_params_frame(self):
        if self.alg.get() == "greedy":
            self.ACO_params_frame.grid_remove()
        else:
            self.ACO_params_frame.grid(row=4, column=0, padx=20, pady=10, sticky="we")

    def __display_problem_params(self, problem_data: dict):
        for p in problem_data:
            self.problem_data_vars[p] = problem_data[p]

    def __generate_problem(self):
        pg_params = self.__parse_validate_problem_generator_params(self.__PROBLEM_GEN_PARAMS_SYS_NAMES,
                                                                   self.__PROBLEM_GEN_PARAMS_UI_NAMES,
                                                                   self.problem_gen_params_vars)
        

    def __open_file(self):
        try:
            path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
            problem_data = self.__parse_validate_file_data(path)
            self.__display_problem_params(problem_data)

        except FileNotFoundError:
            messagebox.showerror("Помилка", "Файл не знайдено")
        except json.JSONDecodeError:
            messagebox.showerror("Помилка", "Файл JSON невалідний")
        except ValueError as e:
            messagebox.showerror("Помилка", str(e))
        
    # def run_individual_problem_solving(self):
    #     random_state = self.__get_validated_seed()
    #     problem_data = self.__get_validated_problem_data(self.__PROBLEM_DATA_SYS_NAMES)
    #     if self.alg.get() == "ACO":
    #         ACO_params = self.__get_validated_ACO_params(self.__ACO_PARAMS_SYS_NAMES)
        
    def __parse_validate_file_data(self, path):
        problem_data = self.controller.load_file(path)
        try:
            problem_data = dict(problem_data)
        except ValueError as e:
            raise ValueError("Верхньою структурою файлу повинен бути словник")
        if set(problem_data.keys()) != set(self.__PROBLEM_DATA_SYS_NAMES):
            raise ValueError("У файлі не вистачає ключів або є зайві")
        return self.__parse_validate_problem_data(self.__PROBLEM_DATA_SYS_NAMES, self.__PROBLEM_DATA_UI_NAMES, problem_data)

    def __parse_validate_problem_data(self, included_params: list, param_names_in_errors: list, data_source: dict):
        all_params_additional_checks = [2, 2, "pos", "pos", 2]
        all_params_check_fns = [self.__parse_array]*2 + [self.__parse_float]*2 + [self.__parse_tuple]
        included_params_indices = [self.__PROBLEM_DATA_SYS_NAMES.index(p) for p in included_params]
        res = {}
        for i in included_params_indices:
            param_name = self.__PROBLEM_DATA_SYS_NAMES[i]
            res[param_name] = all_params_check_fns[i](data_source[param_name], 
                                                      param_names_in_errors[i], 
                                                      all_params_additional_checks[i])
        return res

    def __parse_validate_problem_generator_params(self, included_params: list, param_names_in_errors: list, data_source: dict):
        all_params_sign_checks = [None, "pos", None, "pos", "pos", "pos", "pos", "pos", "non_neg"]
        all_params_check_fns = [self.__parse_float]*8 + [self.__parse_int]
        included_params_indices = [self.__PROBLEM_GEN_PARAMS_SYS_NAMES.index(p) for p in included_params]
        res = {}
        for i in included_params_indices:
            param_name = self.__PROBLEM_GEN_PARAMS_SYS_NAMES[i]
            res[param_name] = all_params_check_fns[i](data_source[param_name], 
                                                        param_names_in_errors[i], 
                                                        all_params_sign_checks[i])
        return res

    def __parse_validate_ACO_params(self, included_params: list, param_names_in_errors: list, data_source: dict):
        all_params_sign_checks = ["non_neg"]*3 + ["pos"]*3
        all_params_check_fns = [self.__parse_float]*4 + [self.__parse_int, self.__parse_float]
        included_params_indices = [self.__ACO_PARAMS_SYS_NAMES.index(p) for p in included_params]
        res = {}
        for i in included_params_indices:
            param_name = self.__ACO_PARAMS_SYS_NAMES[i]
            res[param_name] = all_params_check_fns[i](data_source[param_name], 
                                                      param_names_in_errors[i], 
                                                      all_params_sign_checks[i])
        return res


    def __parse_array(self, value: str, value_name, min_vals_count=0):
        try:
            vals = np.ndarray([np.float64(x) for x in value.split(r"\s*,\s*")])
        except ValueError as e:
            raise ValueError(f"Значення {value_name} має містити тільки числа, розділені комою")
        if len(vals) < min_vals_count: 
            raise ValueError(f"Кількість значень в {value_name} повинна бути не меншою за {min_vals_count}")
    
    def __parse_tuple(self, value: str, value_name, vals_count):
        try:
            vals = (np.float64(x) for x in value.split(r"\s*,\s*"))
        except ValueError as e:
            raise ValueError(f"Значення {value_name} має містити тільки числа, розділені комою")
        if len(vals) < vals_count: 
            raise ValueError(f"Кількість значень в {value_name} повинна бути рівною {vals_count}")

    def __parse_float(self, value, value_name, sign_check=None):
        try:
            value = np.float64(value)
        except ValueError as e:
            raise ValueError(f"Значення {value_name} має бути неперервним")
        self.__check_sign(value, value_name, sign_check)
        return value
    
    def __parse_int(self, value, value_name, sign_check=None):
        try:
            value = np.int64(value)
        except ValueError as e:
            raise ValueError(f"Значення {value_name} має бути цілим")
        self.__check_sign(value, value_name, sign_check)
        return value

    def __check_sign(self, value, value_name, sign_check):
        if sign_check not in self.__SIGN_CHECK_MODES:
            raise ValueError(f"sign_check can be {self.__SIGN_CHECK_MODES}, but it wasn't")
        
        if sign_check is None: return
        if sign_check == "neg" and value >= 0:
            raise ValueError(f"Значення {value_name} повинно бути від'ємним")
        if sign_check == "non_neg" and value < 0:
            raise ValueError(f"Значення {value_name} не може бути від'ємним")
        if sign_check == "non_pos" and value > 0:
            raise ValueError(f"Значення {value_name} не може бути додатнім")
        if sign_check == "pos" and value <= 0:
            raise ValueError(f"Значення {value_name} повинно бути додатнім")
        
    
        

    # def run(self):
    #     coords = self.get_coords()
    #     params = self.get_params()

    #     result = self.controller.run(
    #         self.alg.get(),
    #         coords,
    #         params
    #     )

    #     self.plot(coords, result["path"])
    #     self.result_label.config(text=f"Length: {result['length']}")

    #     if result["history"]:
    #         self.plot_history(result["history"])
    #     else:
    #         self.ax2.clear()
    #         self.canvas2.draw()

