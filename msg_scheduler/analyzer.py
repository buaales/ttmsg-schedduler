import pandas as pd
import networkx
import functools
import matplotlib;

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation


class Analyzer:
    def __init__(self, df: pd.DataFrame, graph: networkx.DiGraph, lcm: int):
        self._df = df
        self._graph = graph
        self._lcm = lcm

    def print_by_time(self):
        print(self._df.sort_values(by='time_slot'))

    def print_by_app(self):
        res = self._df.sort_values(by='app')
        print(res)

    def _animate_update(self, ax, time_slot):
        ax.clear()
        ax.set_title(f'Time slot: {time_slot}')
        edge_lable = dict()
        pos = networkx.spring_layout(self._graph, seed=0, scale=16)
        cur_table = self._df[self._df['time_slot'] == time_slot]
        for idx, cur_row in cur_table.iterrows():
            link = cur_row['link']
            edge_lable[(link.node1.name, link.node2.name)] = cur_row['app'].name

        networkx.draw_networkx_edges(self._graph, pos=pos, ax=ax, edge_color='gray')

        nodes = networkx.draw_networkx_nodes(self._graph, pos=pos, ax=ax, node_color="white", node_size=1000, node_shape='o')
        nodes.set_edgecolor('black')

        networkx.draw_networkx_labels(self._graph, pos=pos, ax=ax, font_size=8)

        networkx.draw_networkx_edge_labels(self._graph, pos=pos, edge_labels=edge_lable, ax=ax)
        ax.set_xticks([])
        ax.set_yticks([])

    def animate(self):
        fig, ax = plt.subplots(figsize=(6, 4))
        ani = animation.FuncAnimation(fig, functools.partial(self._animate_update, ax), frames=self._lcm, interval=1000,
                                      repeat=True)
        plt.show()
        pass
