import tkinter as tk
from controller import Controller
from view import AppView

if __name__ == "__main__":
    root = tk.Tk()
    controller = Controller()
    app = AppView(root, controller)

    root.mainloop()

    # d = {"a":1, "b": [1,2,3], "c":{"g": 45}}
    # keys = set(d.keys())
    # k_2 = set(["c", "b", "a", "h"])
    # print(keys == k_2)


    # rng = np.random.default_rng(42)
    # # prob = UAVPathPlanningProblem(np.array([20, 10, 20, 30, 50, 50, 70, 90, 100]), 
    # #                             np.array([10, 30, 50, 30, 20, 50, 40, 40, 60]),
    # #                             np.float64(100.0), np.float64(1.3), (np.float64(5.0), np.float64(-10.0)))
    # # prob = UAVPathPlanningProblem(rng.uniform(0, 100, 102), rng.uniform(0, 100, 102),
    # #                             np.float64(100), np.float64(5), (np.float64(5), np.float64(-10)))
    # # res = ACO(prob, 0.8, 1, 0.1, 0.01, 5, 2000, 42)
    # # # res = greedy(prob)

    # # print(res.objects_inspected)
    # # print(res.solving_time_sec)

    # # fig, axes = plt.subplots(1, 1, figsize=(10, 8))
    # # axes.scatter(prob.x_coords[1:prob.n_objects+1], prob.y_coords[1:prob.n_objects+1])
    # # axes.scatter(prob.x_coords[[0, prob.n_objects+1]], prob.y_coords[[0, prob.n_objects+1]], c="red")
    # # axes.plot(prob.x_coords[res.route], prob.y_coords[res.route])
    # # plt.show()
    # tfunc = lambda c, m, n: int(c*n*np.log2(n)/m)
    # pg = IndividualProblemGenerator(50, 50, 50, 50,
    #                                 10, 5, 10, 2, random_state)
    # # print(test_specific_param(pg, 1, 0.1, 0.01, 5, tfunc, 25, random_state,
    # #                                  np.linspace(0.1, 2, 10).tolist(), np.arange(5, 30, 5).tolist(), 10, 12,))
    # print(test_time_and_accuracy(pg, 0.8, 1, 0.1, 0.01, 5, tfunc, 25, random_state,
    #                              np.arange(5, 30, 5).tolist(), 10, 12))
