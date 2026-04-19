import os
import json
import re
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, font
from tkinter.scrolledtext import ScrolledText
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns

from controller import Controller


class AppView:
    __SEED_UI_NAME = "Зерно ГПВЧ"
    __N_EXPS_UI_NAME = "K"

    __PROBLEM_DATA_SYS_NAMES = ["x_coords", "y_coords", "UAV_speed", "UAV_flight_time_limit", "wind_vector"]
    __PROBLEM_DATA_UI_NAMES = ["x", "y", "v", "T", "w"]

    __PROBLEM_GEN_PARAMS_SYS_NAMES = ["x_mean", "x_half_interval", "y_mean", "y_half_interval", 
                                      "wind_speed_mean", "wind_speed_half_interval", "UAV_speed_coef", "UAV_flight_time_limit_coef", "n_objects"]
    __PROBLEM_GEN_PARAMS_UI_NAMES = ["x\u0305", "∆x", "y\u0305", "∆y",
                                     "|w\u0305|", "∆w", "rv", "rT", "n"]

    __ACO_PARAMS_SYS_NAMES = ["alpha", "beta", "ro", "initial_pheromone_level", "n_ants_in_pop", "iter_num_func_coef"]
    __ACO_PARAMS_UI_NAMES = ["α", "β", "ρ", "τ\u2080", "μ", "η"]
    __ITER_NUM_FUNC_REPRES = "r=ηnlog(n)/μ"

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
        self.termination_condition_test_tab = ttk.Frame(notebook)
        self.specific_parameter_test_tab = ttk.Frame(notebook)
        self.time_and_accuracy_test_tab = ttk.Frame(notebook)

        notebook.add(self.ind_prob_work_tab, text="Робота з ІЗ")
        notebook.add(self.termination_condition_test_tab, text="Визначення умови завершення роботи ACO")
        notebook.add(self.specific_parameter_test_tab, text="Визначення параметру α ACO")
        notebook.add(self.time_and_accuracy_test_tab, text="Порівняння алгоритмів за часом та точністю")

        style = ttk.Style()
        self.font_size = 12
        self.font = "Aerial"
        default_font = font.nametofont("TkDefaultFont")
        default_font.configure(size=self.font_size)
        style.configure(".", font=(self.font, self.font_size))
        style.configure("My.TFrame", borderwidth=1, relief="solid")

        self.build_ind_prob_work_tab()
        self.build_termination_condition_test_tab()
        self.build_specific_parameter_test_tab()
        self.build_time_and_accuracy_test_tab()

    def build_ind_prob_work_tab(self):
        frame = self.ind_prob_work_tab
        settings_frame = ttk.Frame(frame, style="My.TFrame")
        settings_frame.grid(row=0, column=0, sticky="n")
        graph_frame = ttk.Frame(frame)
        graph_frame.grid(row=0, column=1)
        log_frame = ttk.Frame(frame)
        log_frame.grid(row=0, column=2, sticky="n")

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

        self.save_file_btn = ttk.Button(input_check_frame, text="Зберегти", command=self.__save_to_dir)
        self.save_file_btn.grid(row=5, column=0)


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

        self.gen_prob_btn = ttk.Button(input_check_frame, text="Згенерувати", command=self.__generate_problem)
        
        self.load_file_btn = ttk.Button(input_check_frame, text="Вибрати файл", command=self.__open_file)

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
        ttk.Label(self.ACO_params_frame, text=f"* {self.__ITER_NUM_FUNC_REPRES}").grid(row=len(self.__ACO_PARAMS_SYS_NAMES)+1, column=0, columnspan=2, sticky="w")

        ttk.Button(settings_frame, text="Розв'язати", command=self.__run_individual_problem_solving).grid(row=5, column=0)

        self.fig_sol, self.ax_sol = plt.subplots(figsize=(8,5))
        self.canvas_sol = FigureCanvasTkAgg(self.fig_sol, master=graph_frame)
        self.ax_sol.set_title("Розв'язання ІЗ")
        self.ax_sol.set_xlabel("X")
        self.ax_sol.set_ylabel("Y")
        self.fig_sol.tight_layout()
        self.canvas_sol.get_tk_widget().grid(row=0, column=0)

        self.fig_dynamic, self.ax_dynamic = plt.subplots(figsize=(8,3))
        self.canvas_dynamic = FigureCanvasTkAgg(self.fig_dynamic, master=graph_frame)
        self.ax_dynamic.set_title("Динаміка зміни рекордного розв'язку")
        self.ax_dynamic.set_xlabel("№ ітерації")
        self.ax_dynamic.set_ylabel("Кількість обстежених об'єктів")
        self.fig_dynamic.tight_layout()

        ttk.Label(log_frame, text="Результати роботи алгоритму", 
                  font=(self.font, self.font_size, "bold")).grid(row=0, column=0, sticky="w")
        self.solving_log = ScrolledText(log_frame, width=55, height=30)
        self.solving_log.grid(row=1, column=0)

    def build_termination_condition_test_tab(self):
        frame = self.termination_condition_test_tab
        settings_frame = ttk.Frame(frame, style="My.TFrame")
        settings_frame.grid(row=0, column=0, sticky="n")
        graph_frame = ttk.Frame(frame)
        graph_frame.grid(row=0, column=1)
        log_frame = ttk.Frame(frame)
        log_frame.grid(row=0, column=2, sticky="n")

        # random_state
        random_state_frame = ttk.Frame(settings_frame)
        random_state_frame.grid(row=0, column=0, padx=20, pady=10, sticky="we")
        ttk.Label(random_state_frame, text=self.__SEED_UI_NAME).grid(row=0, column=0, sticky="e")
        self.termination_condition_test_random_state = tk.StringVar()
        e = ttk.Entry(random_state_frame, textvariable=self.termination_condition_test_random_state)
        e.grid(row=0, column=1, padx=10, sticky="e")

        # n_exps
        n_exps_frame = ttk.Frame(settings_frame)
        n_exps_frame.grid(row=1, column=0, padx=20, pady=10, sticky="we")
        ttk.Label(n_exps_frame, text=self.__N_EXPS_UI_NAME).grid(row=1, column=0, sticky="e")
        self.termination_condition_test_n_exps = tk.StringVar()
        e = ttk.Entry(n_exps_frame, textvariable=self.termination_condition_test_n_exps)
        e.grid(row=1, column=1, padx=10, sticky="e")

        # generator_params
        self.termination_condition_test_prob_gen_params_frame = ttk.Frame(settings_frame, style="My.TFrame", borderwidth=1)
        self.termination_condition_test_prob_gen_params_frame.columnconfigure(0, weight=1)
        self.termination_condition_test_prob_gen_params_frame.columnconfigure(1, weight=1)
        self.termination_condition_test_prob_gen_params_frame.grid(row=2, column=0, padx=20, pady=10, sticky="w")
        ttk.Label(self.termination_condition_test_prob_gen_params_frame, text="Параметри генератора ІЗ         ",
                  font=(self.font, self.font_size, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")

        n_exps_vars = self.__create_param_range_input(self.termination_condition_test_prob_gen_params_frame, 
                                                      "problem_sizes", self.__PROBLEM_GEN_PARAMS_UI_NAMES[8],
                                                      row=1)

        fixed_problem_gen_params_sys_names = [p for p in self.__PROBLEM_GEN_PARAMS_SYS_NAMES if p not in ["n_objects"]]
        fixed_problem_gen_params_ui_names = [p for p in self.__PROBLEM_GEN_PARAMS_UI_NAMES if p not in [self.__PROBLEM_GEN_PARAMS_UI_NAMES[8]]]
        problem_generator_fixed_vars, last_row = self.__create_params_table_input(self.termination_condition_test_prob_gen_params_frame, 
                                                          fixed_problem_gen_params_sys_names, fixed_problem_gen_params_ui_names, 
                                                          row_start=2)
        self.termination_condition_test_problem_gen_params_vars = {**n_exps_vars, **problem_generator_fixed_vars}

        # ACO params
        self.termination_condition_test_ACO_params_frame = ttk.Frame(settings_frame, style="My.TFrame", borderwidth=1)
        self.termination_condition_test_ACO_params_frame.columnconfigure(0, weight=1)
        self.termination_condition_test_ACO_params_frame.columnconfigure(1, weight=1)
        self.termination_condition_test_ACO_params_frame.grid(row=3, column=0, padx=20, pady=10, sticky="w")
        ttk.Label(self.termination_condition_test_ACO_params_frame, text="Параметри алгоритму ACO",
                  font=(self.font, self.font_size, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        
        iter_num_func_coefs_vars = self.__create_param_range_input(self.termination_condition_test_ACO_params_frame, 
                                                                   "iter_num_func_coefs", self.__ACO_PARAMS_UI_NAMES[5],
                                                                   row=1)
        fixed_ACO_params_sys_names = [p for p in self.__ACO_PARAMS_SYS_NAMES if p not in ["iter_num_func_coef"]]
        fixed_ACO_params_ui_names = [p for p in self.__ACO_PARAMS_UI_NAMES if p not in [self.__ACO_PARAMS_UI_NAMES[5]]]
        ACO_fixed_vars, last_row = self.__create_params_table_input(self.termination_condition_test_ACO_params_frame, 
                                                                    fixed_ACO_params_sys_names, fixed_ACO_params_ui_names, 
                                                                    row_start=2)        
        self.termination_condition_test_aco_params_vars = {**iter_num_func_coefs_vars, **ACO_fixed_vars}

        ttk.Button(settings_frame, text="Запустити", 
                   command=self.__run_termination_condition_test).grid(row=4, column=0)

        # Stats grahp
        self.fig_termination_condition_test_o_f, self.ax_termination_condition_test_o_f = plt.subplots(figsize=(8,5))
        self.canvas_termination_condition_test_o_f = FigureCanvasTkAgg(self.fig_termination_condition_test_o_f, master=graph_frame)
        self.ax_termination_condition_test_o_f.set_title(
            f"Статистика ЦФ для різних {self.__ACO_PARAMS_UI_NAMES[5]} та {self.__PROBLEM_GEN_PARAMS_UI_NAMES[8]}"
        )
        self.ax_termination_condition_test_o_f.set_xlabel(self.__PROBLEM_GEN_PARAMS_UI_NAMES[8])
        self.ax_termination_condition_test_o_f.set_ylabel("Кількість обстежених об'єктів")
        self.fig_termination_condition_test_o_f.tight_layout()
        self.canvas_termination_condition_test_o_f.get_tk_widget().grid(row=0, column=0)

        # log
        ttk.Label(log_frame, text="Статистика експерименту", 
                  font=(self.font, self.font_size, "bold")).grid(row=0, column=0, sticky="w")
        self.termination_condition_test_log = ScrolledText(log_frame, width=55, height=30)
        self.termination_condition_test_log.grid(row=1, column=0, sticky="e")

    def build_specific_parameter_test_tab(self):
        frame = self.specific_parameter_test_tab
        settings_frame = ttk.Frame(frame, style="My.TFrame")
        settings_frame.grid(row=0, column=0, sticky="n")
        graph_frame = ttk.Frame(frame)
        graph_frame.grid(row=0, column=1)
        log_frame = ttk.Frame(frame)
        log_frame.grid(row=0, column=2, sticky="n")

        # random_state
        random_state_frame = ttk.Frame(settings_frame)
        random_state_frame.grid(row=0, column=0, padx=20, pady=10, sticky="we")
        ttk.Label(random_state_frame, text=self.__SEED_UI_NAME).grid(row=0, column=0, sticky="e")
        self.specific_parameter_test_random_state = tk.StringVar()
        e = ttk.Entry(random_state_frame, textvariable=self.specific_parameter_test_random_state)
        e.grid(row=0, column=1, padx=10, sticky="e")

        # n_exps
        n_exps_frame = ttk.Frame(settings_frame)
        n_exps_frame.grid(row=1, column=0, padx=20, pady=10, sticky="we")
        ttk.Label(n_exps_frame, text=self.__N_EXPS_UI_NAME).grid(row=1, column=0, sticky="e")
        self.specific_parameter_test_n_exps = tk.StringVar()
        e = ttk.Entry(n_exps_frame, textvariable=self.specific_parameter_test_n_exps)
        e.grid(row=1, column=1, padx=10, sticky="e")

        # generator_params
        self.specific_parameter_test_prob_gen_params_frame = ttk.Frame(settings_frame, style="My.TFrame", borderwidth=1)
        self.specific_parameter_test_prob_gen_params_frame.columnconfigure(0, weight=1)
        self.specific_parameter_test_prob_gen_params_frame.columnconfigure(1, weight=1)
        self.specific_parameter_test_prob_gen_params_frame.grid(row=2, column=0, padx=20, pady=10, sticky="w")
        ttk.Label(self.specific_parameter_test_prob_gen_params_frame, text="Параметри генератора ІЗ         ",
                  font=(self.font, self.font_size, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")

        n_exps_vars = self.__create_param_range_input(self.specific_parameter_test_prob_gen_params_frame, 
                                                      "problem_sizes", self.__PROBLEM_GEN_PARAMS_UI_NAMES[8],
                                                      row=1)
        fixed_problem_gen_params_sys_names = [p for p in self.__PROBLEM_GEN_PARAMS_SYS_NAMES if p not in ["n_objects"]]
        fixed_problem_gen_params_ui_names = [p for p in self.__PROBLEM_GEN_PARAMS_UI_NAMES if p not in [self.__PROBLEM_GEN_PARAMS_UI_NAMES[8]]]
        problem_generator_fixed_vars, last_row = self.__create_params_table_input(self.specific_parameter_test_prob_gen_params_frame, 
                                                          fixed_problem_gen_params_sys_names, fixed_problem_gen_params_ui_names, 
                                                          row_start=2)
        self.specific_parameter_test_problem_gen_params_vars = {**n_exps_vars, **problem_generator_fixed_vars}

        # ACO params
        self.specific_parameter_test_ACO_params_frame = ttk.Frame(settings_frame, style="My.TFrame", borderwidth=1)
        self.specific_parameter_test_ACO_params_frame.columnconfigure(0, weight=1)
        self.specific_parameter_test_ACO_params_frame.columnconfigure(1, weight=1)
        self.specific_parameter_test_ACO_params_frame.grid(row=3, column=0, padx=20, pady=10, sticky="w")
        ttk.Label(self.specific_parameter_test_ACO_params_frame, text="Параметри алгоритму ACO",
                  font=(self.font, self.font_size, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")
        
        alphas_vars = self.__create_param_range_input(self.specific_parameter_test_ACO_params_frame, 
                                                      "alphas", self.__ACO_PARAMS_UI_NAMES[0], 
                                                      row=1)
        fixed_ACO_params_sys_names = [p for p in self.__ACO_PARAMS_SYS_NAMES if p not in ["alpha"]]
        fixed_ACO_params_ui_names = [p for p in self.__ACO_PARAMS_UI_NAMES if p not in [self.__ACO_PARAMS_UI_NAMES[0]]]
        ACO_fixed_vars, last_row = self.__create_params_table_input(self.specific_parameter_test_ACO_params_frame, 
                                                                    fixed_ACO_params_sys_names, fixed_ACO_params_ui_names, 
                                                                    row_start=2)        
        self.specific_parameter_test_aco_params_vars = {**alphas_vars, **ACO_fixed_vars}

        ttk.Button(settings_frame, text="Запустити", command=self.__run_specific_parameter_test).grid(row=4, column=0)

        # Stats grahp
        self.fig_specific_parameter_test_o_f, self.ax_specific_parameter_test_o_f = plt.subplots(figsize=(8,5))
        self.canvas_specific_parameter_test_o_f = FigureCanvasTkAgg(self.fig_specific_parameter_test_o_f, master=graph_frame)
        self.ax_specific_parameter_test_o_f.set_title(
            f"Статистика ЦФ для різних {self.__ACO_PARAMS_UI_NAMES[0]} та {self.__PROBLEM_GEN_PARAMS_UI_NAMES[8]}"
        )
        self.ax_specific_parameter_test_o_f.set_xlabel(self.__PROBLEM_GEN_PARAMS_UI_NAMES[8])
        self.ax_specific_parameter_test_o_f.set_ylabel("Кількість обстежених об'єктів")
        self.fig_specific_parameter_test_o_f.tight_layout()
        self.canvas_specific_parameter_test_o_f.get_tk_widget().grid(row=0, column=0)

        # log
        ttk.Label(log_frame, text="Статистика експерименту", 
                  font=(self.font, self.font_size, "bold")).grid(row=0, column=0, sticky="w")
        self.specific_parameter_test_log = ScrolledText(log_frame, width=55, height=30)
        self.specific_parameter_test_log.grid(row=1, column=0, sticky="e")

    def build_time_and_accuracy_test_tab(self):
        frame = self.time_and_accuracy_test_tab
        settings_frame = ttk.Frame(frame, style="My.TFrame")
        settings_frame.grid(row=0, column=0, sticky="n")
        graph_frame = ttk.Frame(frame)
        graph_frame.grid(row=0, column=1)
        log_frame = ttk.Frame(frame)
        log_frame.grid(row=0, column=2, sticky="n")

        # random_state
        random_state_frame = ttk.Frame(settings_frame)
        random_state_frame.grid(row=0, column=0, padx=20, pady=10, sticky="we")
        ttk.Label(random_state_frame, text=self.__SEED_UI_NAME).grid(row=0, column=0, sticky="e")
        self.time_and_accuracy_test_random_state = tk.StringVar()
        e = ttk.Entry(random_state_frame, textvariable=self.time_and_accuracy_test_random_state)
        e.grid(row=0, column=1, padx=10, sticky="e")

        # n_exps
        n_exps_frame = ttk.Frame(settings_frame)
        n_exps_frame.grid(row=1, column=0, padx=20, pady=10, sticky="we")
        ttk.Label(n_exps_frame, text=self.__N_EXPS_UI_NAME).grid(row=1, column=0, sticky="e")
        self.time_and_accuracy_test_n_exps = tk.StringVar()
        e = ttk.Entry(n_exps_frame, textvariable=self.time_and_accuracy_test_n_exps)
        e.grid(row=1, column=1, padx=10, sticky="e")

        # generator_params
        self.time_and_accuracy_test_prob_gen_params_frame = ttk.Frame(settings_frame, style="My.TFrame", borderwidth=1)
        self.time_and_accuracy_test_prob_gen_params_frame.columnconfigure(0, weight=1)
        self.time_and_accuracy_test_prob_gen_params_frame.columnconfigure(1, weight=1)
        self.time_and_accuracy_test_prob_gen_params_frame.grid(row=2, column=0, padx=20, pady=10, sticky="w")
        ttk.Label(self.time_and_accuracy_test_prob_gen_params_frame, text="Параметри генератора ІЗ         ",
                  font=(self.font, self.font_size, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")

        n_objects_vars = self.__create_param_range_input(self.time_and_accuracy_test_prob_gen_params_frame, 
                                                         "problem_sizes", self.__PROBLEM_GEN_PARAMS_UI_NAMES[8], 
                                                         row=1)
        fixed_problem_gen_params_sys_names = [p for p in self.__PROBLEM_GEN_PARAMS_SYS_NAMES if p not in ["n_objects"]]
        fixed_problem_gen_params_ui_names = [p for p in self.__PROBLEM_GEN_PARAMS_UI_NAMES if p not in [self.__PROBLEM_GEN_PARAMS_UI_NAMES[8]]]
        problem_generator_fixed_vars, last_row = self.__create_params_table_input(self.time_and_accuracy_test_prob_gen_params_frame, 
                                                          fixed_problem_gen_params_sys_names, fixed_problem_gen_params_ui_names, 
                                                          row_start=2)
        self.time_and_accuracy_test_problem_gen_params_vars = {**n_objects_vars, **problem_generator_fixed_vars}

        # ACO params
        self.time_and_accuracy_test_ACO_params_frame = ttk.Frame(settings_frame, style="My.TFrame", borderwidth=1)
        self.time_and_accuracy_test_ACO_params_frame.columnconfigure(0, weight=1)
        self.time_and_accuracy_test_ACO_params_frame.columnconfigure(1, weight=1)
        self.time_and_accuracy_test_ACO_params_frame.grid(row=3, column=0, padx=20, pady=10, sticky="w")
        ttk.Label(self.time_and_accuracy_test_ACO_params_frame, text="Параметри алгоритму ACO",
                  font=(self.font, self.font_size, "bold")).grid(row=0, column=0, columnspan=2, sticky="w")        
        ACO_fixed_vars, last_row = self.__create_params_table_input(self.time_and_accuracy_test_ACO_params_frame, 
                                                                    self.__ACO_PARAMS_SYS_NAMES, self.__ACO_PARAMS_UI_NAMES, 
                                                                    row_start=1)        
        self.time_and_accuracy_test_aco_params_vars = ACO_fixed_vars

        ttk.Button(settings_frame, text="Запустити", command=self.__run_time_and_accuracy_test).grid(row=4, column=0)
        
        # Stats grahp
        self.fig_accuracy, self.ax_accuracy = plt.subplots(figsize=(8,5))
        self.canvas_accuracy = FigureCanvasTkAgg(self.fig_accuracy, master=graph_frame)
        self.ax_accuracy.set_title(f"Точність алгоритмів для різних {self.__PROBLEM_GEN_PARAMS_UI_NAMES[8]}")
        self.ax_accuracy.set_xlabel(self.__PROBLEM_GEN_PARAMS_UI_NAMES[8])
        self.ax_accuracy.set_ylabel("Кількість обстежених об'єктів")
        self.fig_accuracy.tight_layout()
        self.canvas_accuracy.get_tk_widget().grid(row=0, column=0)

        self.fig_time, self.ax_time = plt.subplots(figsize=(8,4))
        self.canvas_time = FigureCanvasTkAgg(self.fig_time, master=graph_frame)
        self.ax_time.set_title(f"Час роботи алгоритмів для різних {self.__PROBLEM_GEN_PARAMS_UI_NAMES[8]}")
        self.ax_time.set_xlabel(self.__PROBLEM_GEN_PARAMS_UI_NAMES[8])
        self.ax_time.set_ylabel("с")
        self.fig_time.tight_layout()
        self.canvas_time.get_tk_widget().grid(row=1, column=0)

        # log
        ttk.Label(log_frame, text="Статистика за точністю", 
                  font=(self.font, self.font_size, "bold")).grid(row=0, column=0, sticky="w")
        self.accuracy_test_log = ScrolledText(log_frame, width=80, height=25)
        self.accuracy_test_log.grid(row=1, column=0, sticky="e")

        ttk.Label(log_frame, text="Статистика за часом", 
                  font=(self.font, self.font_size, "bold")).grid(row=2, column=0, sticky="w")
        self.time_test_log = ScrolledText(log_frame, width=80, height=25)
        self.time_test_log.grid(row=3, column=0, sticky="e")


    def __run_individual_problem_solving(self):
        try:            
            problem_data = self.__parse_validate_problem_data(self.__PROBLEM_DATA_SYS_NAMES, 
                                                              self.__PROBLEM_DATA_UI_NAMES, 
                                                              {k: self.problem_data_vars[k].get() for k in self.problem_data_vars})
            if self.alg.get() == "greedy":
                greedy_solution = self.controller.run_greedy(problem_data)
                self.__visualize_route(problem_data, greedy_solution)
                self.__log_result(problem_data, greedy_solution, "ЖА")
            else:
                random_state = self.__parse_int(self.random_state.get(), self.__SEED_UI_NAME)
                ACO_params = self.__parse_validate_ACO_params(self.__ACO_PARAMS_SYS_NAMES, 
                                                              {k: self.ACO_params_vars[k].get() for k in self.ACO_params_vars})
                ACO_solution = self.controller.run_ACO(problem_data, ACO_params, random_state)
                self.__visualize_route(problem_data, ACO_solution)
                self.__visualize_sol_dynamic(ACO_solution)
                self.__log_result(problem_data, ACO_solution, "ACO")
        except ValueError as e:
            messagebox.showerror("Помилка", str(e))

    def __run_termination_condition_test(self):
        try:
            random_state = self.__parse_int(self.termination_condition_test_random_state.get(), self.__SEED_UI_NAME)
            n_exps = self.__parse_int(self.termination_condition_test_n_exps.get(),
                                      self.__N_EXPS_UI_NAME, 
                                      sign_check="pos")

            problem_sizes_range = self.__parse_int_range(
                self.__PROBLEM_GEN_PARAMS_UI_NAMES[8], 
                {k: self.termination_condition_test_problem_gen_params_vars["problem_sizes"][k].get() 
                 for k in self.termination_condition_test_problem_gen_params_vars["problem_sizes"]}, 
                 sign_check="pos"
            )
            problem_generator_params = self.__parse_validate_problem_generator_params(
                [p for p in self.__PROBLEM_GEN_PARAMS_SYS_NAMES if p not in ["n_objects"]],
                [p for p in self.__PROBLEM_GEN_PARAMS_UI_NAMES if p not in [self.__PROBLEM_GEN_PARAMS_UI_NAMES[8]]],
                {k:self.termination_condition_test_problem_gen_params_vars[k].get() 
                 for k in self.termination_condition_test_problem_gen_params_vars 
                 if k != "problem_sizes"}
            )
            iter_num_func_coefs_range = self.__parse_float_range(
                self.__ACO_PARAMS_UI_NAMES[5], 
                {k:self.termination_condition_test_aco_params_vars["iter_num_func_coefs"][k].get() 
                 for k in self.termination_condition_test_aco_params_vars["iter_num_func_coefs"]},
                sign_check="pos"
            )
            ACO_params = self.__parse_validate_ACO_params(
                [p for p in self.__ACO_PARAMS_SYS_NAMES if p not in ["iter_num_func_coef"]], 
                {k: self.termination_condition_test_aco_params_vars[k].get() 
                 for k in self.termination_condition_test_aco_params_vars
                 if k != "iter_num_func_coefs"}
            )

            exp_data = self.controller.run_termination_condition_experiment(problem_sizes_range, problem_generator_params, 
                                                                            iter_num_func_coefs_range, ACO_params, n_exps, random_state)
            self.__visualize_termination_condition_test_results(exp_data)
            self.__log_termination_condition_test_stats(exp_data)
        except ValueError as e:
            messagebox.showerror("Помилка", str(e))

    def __run_specific_parameter_test(self):
        try:
            random_state = self.__parse_int(self.specific_parameter_test_random_state.get(), self.__SEED_UI_NAME)
            n_exps = self.__parse_int(self.specific_parameter_test_n_exps.get(),
                                      self.__N_EXPS_UI_NAME, 
                                      sign_check="pos")
            problem_sizes_range = self.__parse_int_range(
                self.__PROBLEM_GEN_PARAMS_UI_NAMES[8], 
                {k: self.specific_parameter_test_problem_gen_params_vars["problem_sizes"][k].get() 
                 for k in self.specific_parameter_test_problem_gen_params_vars["problem_sizes"]}, 
                sign_check="pos"
            )
            problem_generator_params = self.__parse_validate_problem_generator_params(
                [p for p in self.__PROBLEM_GEN_PARAMS_SYS_NAMES if p not in ["n_objects"]],
                [p for p in self.__PROBLEM_GEN_PARAMS_UI_NAMES if p not in [self.__PROBLEM_GEN_PARAMS_UI_NAMES[8]]],
                {k:self.specific_parameter_test_problem_gen_params_vars[k].get() 
                 for k in self.specific_parameter_test_problem_gen_params_vars 
                 if k != "problem_sizes"}
            )
            alphas_range = self.__parse_float_range(
                self.__ACO_PARAMS_UI_NAMES[0], 
                {k:self.specific_parameter_test_aco_params_vars["alphas"][k].get() 
                 for k in self.specific_parameter_test_aco_params_vars["alphas"]},
                sign_check="non_neg"
            )
            ACO_params = self.__parse_validate_ACO_params(
                [p for p in self.__ACO_PARAMS_SYS_NAMES if p not in ["alpha"]], 
                {k: self.specific_parameter_test_aco_params_vars[k].get() 
                 for k in self.specific_parameter_test_aco_params_vars
                 if k != "alphas"}
            )

            exp_data = self.controller.run_specific_parameter_experiment(problem_sizes_range, problem_generator_params, 
                                                                         alphas_range, ACO_params, n_exps, random_state)
            self.__visualize_specific_parameter_test_results(exp_data)
            self.__log_specific_parameter_test_stats(exp_data)
        except ValueError as e:
            messagebox.showerror("Помилка", str(e))

    def __run_time_and_accuracy_test(self):
        try:
            random_state = self.__parse_int(self.time_and_accuracy_test_random_state.get(), self.__SEED_UI_NAME)
            n_exps = self.__parse_int(self.time_and_accuracy_test_n_exps.get(), 
                                      self.__N_EXPS_UI_NAME, 
                                      sign_check="pos")
            problem_sizes_range = self.__parse_int_range(
                self.__PROBLEM_GEN_PARAMS_UI_NAMES[8], 
                {k: self.time_and_accuracy_test_problem_gen_params_vars["problem_sizes"][k].get() 
                 for k in self.time_and_accuracy_test_problem_gen_params_vars["problem_sizes"]}, 
                sign_check="pos"
            )
            problem_generator_params = self.__parse_validate_problem_generator_params(
                [p for p in self.__PROBLEM_GEN_PARAMS_SYS_NAMES if p not in ["n_objects"]],
                [p for p in self.__PROBLEM_GEN_PARAMS_UI_NAMES if p not in [self.__PROBLEM_GEN_PARAMS_UI_NAMES[8]]],
                {k:self.time_and_accuracy_test_problem_gen_params_vars[k].get() 
                 for k in self.time_and_accuracy_test_problem_gen_params_vars 
                 if k != "problem_sizes"}
            )
            ACO_params = self.__parse_validate_ACO_params(
                self.__ACO_PARAMS_SYS_NAMES, 
                {k: self.time_and_accuracy_test_aco_params_vars[k].get() 
                 for k in self.time_and_accuracy_test_aco_params_vars}
            )

            exp_data = self.controller.run_time_and_accuracy_experiment(problem_sizes_range, problem_generator_params, 
                                                                        ACO_params, n_exps, random_state)
            self.__visualize_time_and_accuracy_test_results(exp_data)
            self.__log_time_and_accuracy_test_stats(exp_data)
        except ValueError as e:
            messagebox.showerror("Помилка", str(e))


    def __visualize_route(self, problem_data: dict, solution):
        n_objects = len(problem_data["x_coords"]) - 2
        self.ax_sol.clear()        
        self.ax_sol.scatter(problem_data["x_coords"][1:n_objects+1], problem_data["y_coords"][1:n_objects+1], c="blue")
        self.ax_sol.scatter(problem_data["x_coords"][[0, n_objects+1]], problem_data["y_coords"][[0, n_objects+1]], 
                            marker="s", s=50, c="orange", label="Пункти зльоту-посадки")
        label_y_shift = 2*(problem_data["x_coords"].max() - problem_data["x_coords"].min()) / 100
        for i, x, y in zip(range(n_objects+2), problem_data["x_coords"], problem_data["y_coords"]):
            self.ax_sol.text(x, y-label_y_shift, str(i))

        self.ax_sol.plot(problem_data["x_coords"][solution.route], problem_data["y_coords"][solution.route], c="green")
        self.ax_sol.set_title("Розв'язання ІЗ")
        self.ax_sol.set_xlabel("X")
        self.ax_sol.set_ylabel("Y")
        self.ax_sol.legend()
        self.fig_sol.tight_layout()
        self.canvas_sol.draw()

    def __visualize_sol_dynamic(self, solution):
        n_iters = len(solution.iter_best_objects_inspected_dynamic)
        iter_nums = np.arange(1, n_iters+1)
        self.ax_dynamic.clear() 
        self.ax_dynamic.plot(iter_nums, solution.iter_best_objects_inspected_dynamic, 
                             c="blue", label="Кращий розв'язок поточної ітерації")
        self.ax_dynamic.plot(iter_nums, solution.record_best_objects_inspected_dynamic,
                             c="orange", label="Рекордний розв'язок")
        self.ax_dynamic.set_title("Динаміка зміни рекордного розв'язку")
        self.ax_dynamic.set_xlabel("№ ітерації")
        self.ax_dynamic.set_ylabel("Кількість обстежених об'єктів")
        self.ax_dynamic.legend()
        self.fig_dynamic.tight_layout()
        self.canvas_dynamic.draw()

    def __log_result(self, problem_data, solution, alg_name):
        self.solving_log.insert("end", f"""================= Звіт {alg_name} =================
розмірність задачі: {len(problem_data["x_coords"])-2} об'єктів
час роботи: {solution.solving_time_sec:.6f} с
знайдений маршрут: {", ".join(map(str, solution.route))}
кількість обстежених об'єктів: {solution.objects_inspected}

""")
        self.solving_log.see("end")

    def __visualize_termination_condition_test_results(self, exp_data):
        exp_data["iter_num_func_coef"] = exp_data["iter_num_func_coef"].round(5).astype(str)
        self.ax_termination_condition_test_o_f.clear()
        ax = sns.lineplot(
            data=exp_data,
            x="problem_size",
            y="objective_function",
            hue="iter_num_func_coef",
            errorbar="ci",
            ax=self.ax_termination_condition_test_o_f
        )
        ax.legend(title=self.__ACO_PARAMS_UI_NAMES[5])
        self.ax_termination_condition_test_o_f.set_xlabel(self.__PROBLEM_GEN_PARAMS_UI_NAMES[8])
        self.ax_termination_condition_test_o_f.set_ylabel("Кількість обстежених об'єктів")
        self.fig_termination_condition_test_o_f.tight_layout()
        self.canvas_termination_condition_test_o_f.draw()

    def __log_termination_condition_test_stats(self, exp_data):
        stats_df = exp_data.groupby(
            ["iter_num_func_coef", "problem_size"], 
            as_index=False
        ).agg(
            mean_obj=("objective_function", "mean"),
            std_obj=("objective_function", "std")
        )
        stats_df.columns = [
            self.__ACO_PARAMS_UI_NAMES[5],
            self.__PROBLEM_GEN_PARAMS_UI_NAMES[8],
            "сер. знач. ЦФ",
            "станд. відхил. ЦФ"
        ]

        self.termination_condition_test_log.insert("end", f"===============================================\n{stats_df.to_string()}\n\n")
        self.termination_condition_test_log.see("end")
        
    def __visualize_specific_parameter_test_results(self, exp_data):
        exp_data["alpha"] = exp_data["alpha"].round(5).astype(str)
        self.ax_specific_parameter_test_o_f.clear()
        ax = sns.lineplot(
            data=exp_data,
            x="problem_size",
            y="objective_function",
            hue="alpha",
            errorbar="ci",
            ax=self.ax_specific_parameter_test_o_f
        )
        ax.legend(title=self.__ACO_PARAMS_UI_NAMES[0])
        self.ax_specific_parameter_test_o_f.set_xlabel(self.__PROBLEM_GEN_PARAMS_UI_NAMES[8])
        self.ax_specific_parameter_test_o_f.set_ylabel("Кількість обстежених об'єктів")
        self.fig_specific_parameter_test_o_f.tight_layout()
        self.canvas_specific_parameter_test_o_f.draw()

    def __log_specific_parameter_test_stats(self, exp_data):
        stats_df = exp_data.groupby(
            ["alpha", "problem_size"], 
            as_index=False
        ).agg(
            mean_obj=("objective_function", "mean"),
            std_obj=("objective_function", "std")
        )
        stats_df.columns = [
            self.__ACO_PARAMS_UI_NAMES[0],
            self.__PROBLEM_GEN_PARAMS_UI_NAMES[8],
            "сер. знач. ЦФ",
            "станд. відхил. ЦФ"
        ]
        self.specific_parameter_test_log.insert("end", f"===============================================\n{stats_df.to_string()}\n\n")
        self.specific_parameter_test_log.see("end")

    def __visualize_time_and_accuracy_test_results(self, exp_data):
        self.ax_accuracy.clear()
        ax_acc = sns.lineplot(
            data=exp_data[["problem_size", "greedy_objective_function"]],
            x="problem_size",
            y="greedy_objective_function",
            label="ЖА",
            errorbar="ci",
            ax=self.ax_accuracy
        )
        ax_acc = sns.lineplot(
            data=exp_data[["problem_size", "ACO_objective_function"]],
            x="problem_size",
            y="ACO_objective_function",
            label="ACO",
            errorbar="ci",
            ax=self.ax_accuracy
        )
        ax_acc = sns.lineplot(
            data=exp_data[["problem_size", "delta"]],
            x="problem_size",
            y="delta",
            label="δ",
            errorbar="ci",
            ax=self.ax_accuracy
        )
        self.ax_accuracy.set_title(f"Точність алгоритмів для різних {self.__PROBLEM_GEN_PARAMS_UI_NAMES[8]}")
        self.ax_accuracy.set_xlabel(self.__PROBLEM_GEN_PARAMS_UI_NAMES[8])
        self.ax_accuracy.set_ylabel("Кількість обстежених об'єктів")
        self.fig_accuracy.tight_layout()
        self.canvas_accuracy.draw()

        self.ax_time.clear()
        ax_time = sns.lineplot(
            data=exp_data[["problem_size", "greedy_solving_time_sec"]],
            x="problem_size",
            y="greedy_solving_time_sec",
            label="ЖА",
            errorbar="ci",
            ax=self.ax_time
        )
        ax_time = sns.lineplot(
            data=exp_data[["problem_size", "ACO_solving_time_sec"]],
            x="problem_size",
            y="ACO_solving_time_sec",
            label="ACO",
            errorbar="ci",
            ax=self.ax_time
        )
        self.ax_time.set_title(f"Час роботи алгоритмів для різних {self.__PROBLEM_GEN_PARAMS_UI_NAMES[8]}")
        self.ax_time.set_xlabel(self.__PROBLEM_GEN_PARAMS_UI_NAMES[8])
        self.ax_time.set_ylabel("с")
        self.fig_time.tight_layout()
        self.canvas_time.draw()        

    def __log_time_and_accuracy_test_stats(self, exp_data):
        accuracy_stats_df = exp_data.groupby("problem_size", as_index=False).agg(
            greedy_obj_mean=("greedy_objective_function", "mean"),
            greedy_obj_std=("greedy_objective_function", "std"),
            ACO_obj_mean=("ACO_objective_function", "mean"),
            ACO_obj_std=("ACO_objective_function", "std"),
            delta_mean=("delta", "mean"),
            delta_std=("delta", "std")
        )
        accuracy_stats_df.columns = [
            self.__PROBLEM_GEN_PARAMS_UI_NAMES[8],
            "ЦФ ЖА сер.",
            "ЦФ ЖА ст.в.",
            "ЦФ ACO сер.",
            "ЦФ ACO ст.в.",
            "δ сер.",
            "δ ст.в.",
        ]
        self.accuracy_test_log.insert("end", f"=============================================================================\n{accuracy_stats_df.to_string()}\n\n")
        self.accuracy_test_log.see("end")

        time_stats_df = exp_data.groupby("problem_size", as_index=False).agg(
            greedy_time_mean=("greedy_solving_time_sec", "mean"),
            greedy_time_std=("greedy_solving_time_sec", "std"),
            ACO_time_mean=("ACO_solving_time_sec", "mean"),
            ACO_time_std=("ACO_solving_time_sec", "std")
        )
        time_stats_df.columns = [
            self.__PROBLEM_GEN_PARAMS_UI_NAMES[8],
            "час ЖА сер.",
            "час ЖА ст.в.",
            "час ACO сер.",
            "час ACO ст.в."
        ]
        self.time_test_log.insert("end", f"=============================================================================\n{time_stats_df.to_string()}\n\n")
        self.time_test_log.see("end")


    def __create_param_range_input(self, parent, param_sys_name, param_ui_name, row):
        entry_with = 5
        entry_padx = 10
        input_frame = ttk.Frame(parent)
        input_frame.grid(row=row, column=0, columnspan=2, sticky="w")
        ttk.Label(input_frame, text=param_ui_name).grid(row=row, column=0, sticky="e")
        ttk.Label(input_frame, text="від").grid(row=1, column=1, sticky="e")
        from_var = tk.StringVar()
        e = ttk.Entry(input_frame, width=entry_with, textvariable=from_var)
        e.grid(row=row, column=2, padx=entry_padx, sticky="e")
        ttk.Label(input_frame, text="до (вкл)").grid(row=row, column=3, sticky="e")
        to_var = tk.StringVar()
        e = ttk.Entry(input_frame, width=entry_with, textvariable=to_var)
        e.grid(row=row, column=4, padx=entry_padx, sticky="e")
        ttk.Label(input_frame, text="крок").grid(row=row, column=5, sticky="e")
        step_var = tk.StringVar()
        e = ttk.Entry(input_frame, width=entry_with, textvariable=step_var)
        e.grid(row=row, column=6, padx=entry_padx, sticky="e")
        return {
            param_sys_name: {
                "from": from_var,
                "to": to_var,
                "step": step_var
            }
        }       

    def __create_params_table_input(self, parent, params_sys_names, params_ui_names, row_start=0):
        vars = {}
        for i, p_sys, p_ui in zip(range(len(params_sys_names)), 
                                  params_sys_names, params_ui_names):
            ttk.Label(parent, text=p_ui).grid(row=i+row_start, column=0, sticky="e")
            var = tk.StringVar()
            e = ttk.Entry(parent, textvariable=var)
            e.grid(row=i+row_start, column=1, padx=10, sticky="e")
            vars[p_sys] = var
        last_row = row_start + len(params_sys_names)-1
        return (vars, last_row)

    def __update_additional_input(self):
        if self.input_mode.get() == "manual":
            self.prob_input_frame.grid(row=4, column=0, pady=10, sticky="we")
            self.save_file_btn.grid(row=5, column=0)
        else:
            self.prob_input_frame.grid_remove()
            self.save_file_btn.grid_remove()

        if self.input_mode.get() == "file":
            self.load_file_btn.grid(row=4, column=0)
        else:
            self.load_file_btn.grid_remove()

        if self.input_mode.get() == "generate":
            self.prob_gen_params_frame.grid(row=4, column=0, pady=10, sticky="we")
            self.gen_prob_btn.grid(row=5, column=0)
        else:
            self.prob_gen_params_frame.grid_remove()
            self.gen_prob_btn.grid_remove()

    def __update_ACO_params_frame(self):
        if self.alg.get() == "greedy":
            self.ACO_params_frame.grid_remove()
            self.canvas_dynamic.get_tk_widget().grid_remove()
        else:
            self.ACO_params_frame.grid(row=4, column=0, padx=20, pady=10, sticky="we")
            self.canvas_dynamic.get_tk_widget().grid(row=1, column=0)

    def __display_problem_params(self, problem_data: dict):
        problem_data["x_coords"] = ", ".join(map(str, problem_data["x_coords"]))
        problem_data["y_coords"] = ", ".join(map(str, problem_data["y_coords"]))
        problem_data["wind_vector"] = f"{problem_data["wind_vector"][0]}, {problem_data["wind_vector"][1]}"
        for p in problem_data:
            self.problem_data_vars[p].set(problem_data[p])
        self.input_mode.set("manual")
        self.__update_additional_input()


    def __generate_problem(self):
        try:
            random_state = self.__parse_int(self.random_state.get(), self.__SEED_UI_NAME)
            pg_params = self.__parse_validate_problem_generator_params(self.__PROBLEM_GEN_PARAMS_SYS_NAMES,
                                                                    self.__PROBLEM_GEN_PARAMS_UI_NAMES,
                                                                    {k:self.problem_gen_params_vars[k].get() for k in self.problem_gen_params_vars})
            problem_data = self.controller.get_generated_problem(pg_params, random_state)
            self.__display_problem_params(problem_data)
        except ValueError as e:
            messagebox.showerror("Помилка", str(e))

    def __open_file(self):
        try:
            path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
            if path:
                problem_data = self.__parse_validate_file_data(path)
                self.__display_problem_params(problem_data)
        except FileNotFoundError:
            messagebox.showerror("Помилка", "Файл не знайдено")
        except json.JSONDecodeError:
            messagebox.showerror("Помилка", "Файл JSON невалідний")
        except ValueError as e:
            messagebox.showerror("Помилка", str(e))
    
    def __save_to_dir(self):
        try:
            problem_data = self.__parse_validate_problem_data(self.__PROBLEM_DATA_SYS_NAMES, 
                                                                    self.__PROBLEM_DATA_UI_NAMES, 
                                                                    {k: self.problem_data_vars[k].get() for k in self.problem_data_vars})
            problem_data["x_coords"] = problem_data["x_coords"].tolist()
            problem_data["y_coords"] = problem_data["y_coords"].tolist()
            problem_data["wind_vector"] = list(problem_data["wind_vector"])

            path = filedialog.asksaveasfilename(filetypes=[("JSON files", "*.json")])
            if path:
                if not path.endswith(".json"):
                    path += ".json"
                # if os.path.exists(path):
                #     overwrite = messagebox.askyesno("Файл існує", "Файл вже існує. Перезаписати?")
                #     if not overwrite: return
                self.controller.save_file(path, problem_data)
        except FileNotFoundError:
            messagebox.showerror("Помилка", "Директорію не знайдено")
        except ValueError as e:
            messagebox.showerror("Помилка", str(e))

        
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
        if len(res["x_coords"]) != len(res["y_coords"]):
            raise ValueError("Кількість значень в x та y повинна бути однаковою")
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
        if res["wind_speed_mean"] < res["wind_speed_half_interval"]:
            raise ValueError(f"Значення {self.__PROBLEM_GEN_PARAMS_UI_NAMES[4]} не може бути меншим за {self.__PROBLEM_GEN_PARAMS_UI_NAMES[5]}")
        return res

    def __parse_validate_ACO_params(self, included_params: list, data_source: dict):
        all_params_sign_checks = ["non_neg"]*3 + ["pos"]*3
        all_params_check_fns = [self.__parse_float]*4 + [self.__parse_int, self.__parse_float]
        included_params_indices = [self.__ACO_PARAMS_SYS_NAMES.index(p) for p in included_params]
        res = {}
        for i in included_params_indices:
            param_name = self.__ACO_PARAMS_SYS_NAMES[i]
            res[param_name] = all_params_check_fns[i](data_source[param_name], 
                                                      self.__ACO_PARAMS_UI_NAMES[i],
                                                      all_params_sign_checks[i])
        return res

    def __parse_int_range(self, param_ui_name: str, data_source: dict, sign_check=None):
        vals = {
            "from": self.__parse_int(data_source["from"], f"мінімальне значення {param_ui_name}", sign_check),
            "to": self.__parse_int(data_source["to"], f"максимальне значення {param_ui_name}", sign_check),
            "step": self.__parse_int(data_source["step"], f"крок {param_ui_name}", sign_check="pos"),
        }
        if vals["from"] > vals["to"]:
            raise ValueError(f"Мінімальне значення {param_ui_name} не боже бути більшим за його максимальне значення")
        return vals
    
    def __parse_float_range(self, param_ui_name: str, data_source: dict, sign_check=None):
        vals = {
            "from": self.__parse_float(data_source["from"], f"мінімальне значення {param_ui_name}", sign_check),
            "to": self.__parse_float(data_source["to"], f"максимальне значення {param_ui_name}", sign_check),
            "step": self.__parse_float(data_source["step"], f"крок {param_ui_name}", sign_check="pos"),
        }
        if vals["from"] > vals["to"]:
            raise ValueError(f"Мінімальне значення {param_ui_name} не боже бути більшим за його максимальне значення")
        return vals

    def __parse_array(self, value, value_name, min_vals_count=0):
        try:
            if isinstance(value, (list, tuple, np.ndarray)):
                vals = np.array(value, dtype=np.float64)
            else:
                vals = np.array([np.float64(x) for x in re.split(r"\s*,\s*", value)])
        except ValueError as e:
            raise ValueError(f"Значення {value_name} має містити тільки числа, розділені комою")
        if len(vals) < min_vals_count: 
            raise ValueError(f"Кількість значень в {value_name} повинна бути не меншою за {min_vals_count}")
        return vals
    
    def __parse_tuple(self, value, value_name, vals_count):
        try:
            if isinstance(value, (list, tuple)):
                vals = tuple(value)
            elif isinstance(value, (np.ndarray,)):
                vals = tuple(value.tolist())
            else:
                vals = tuple([np.float64(x) for x in re.split(r"\s*,\s*", value)])
        except ValueError as e:
            raise ValueError(f"Значення {value_name} має містити тільки числа, розділені комою")
        if len(list(vals)) < vals_count: 
            raise ValueError(f"Кількість значень в {value_name} повинна бути рівною {vals_count}")
        return vals

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
