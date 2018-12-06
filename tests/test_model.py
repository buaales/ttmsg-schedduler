import unittest
from msg_scheduler import model, constrains, analyzer


class TestModel(unittest.TestCase):
    def test_topo(self):
        network: model.Network = model.Network()
        for x in range(ord('a'), ord('g')):
            node = model.EndNode('node_' + chr(x))
            network.add_node(node)
        network.add_node(model.SwitchNode('switch_a'))
        network.add_node(model.SwitchNode('switch_b'))

        x = network.get_link_helper()
        x('switch_a', ['node_a', 'node_b', 'node_c', 'switch_b'])
        x('switch_b', ['node_f', 'node_e', 'node_d'])

        app1 = model.Application(network, 'app1', 'node_a')
        app1.set_virtual_link([])

        app2 = model.Application(network, 'app2', 'node_f')
        app2.set_virtual_link([app1])

    def test_director(self):
        # 星形拓扑
        network: model.Network = model.Network()
        for x in range(ord('a'), ord('d')):
            node = model.EndNode('node_' + chr(x))
            network.add_node(node)
        network.add_node(model.SwitchNode('switch_a'))
        network.get_link_helper()('switch_a', ['node_a', 'node_b', 'node_c'])
        # 开始构建约束

        app1 = model.Application(network, 'app1', 'node_a')
        app2 = model.Application(network, 'app2', 'node_b')
        app3 = model.Application(network, 'app3', 'node_c')

        app1.set_virtual_link([app2, app3])
        app2.set_virtual_link([app3])

        app1.set_frame(4, 4)
        app2.set_frame(4, 2)

        app2.depend_on(app1)

        sc = model.Scheduler(network)
        sc.add_apps([app1, app2, app3])

        hook = constrains.Z3Hook()
        sc.add_constrains(hook)
        df = hook.to_dataframe()
        an = analyzer.Analyzer(df, network.graph, sc.app_lcm)
        an.print_by_time()

    def test_paper(self):
        network: model.Network = model.Network()
        # 创建多核处理器
        for proc_idx in range(1, 4):
            msg_node = model.SwitchNode(f'msg_core_{proc_idx}')
            network.add_node(msg_node)

            app_nodes = [model.EndNode(f'app_core_{proc_idx}_{core_idx}') for core_idx in range(1, 4)]
            for n in app_nodes:
                network.add_node(n)
                network.add_link(msg_node.name, n.name)

        switch = model.SwitchNode('switch', 1)
        network.add_node(switch)
        for i in range(1, 4):
            network.add_link(switch.name, f'msg_core_{i}')

        # 生成APP
        apps = {}
        for proc_idx in range(1, 4):
            for core_idx in range(1, 4):
                app = model.Application(network, f'app{proc_idx}_{core_idx}', f'app_core_{proc_idx}_{core_idx}')
                apps[app.name] = app

        # 建立虚链路
        apps['app1_1'].set_virtual_link([apps['app3_2']]).set_frame(4)
        apps['app1_2'].set_virtual_link([apps['app2_2'], apps['app3_1']]).set_frame(8)
        apps['app1_3'].set_virtual_link([apps['app2_3']]).set_frame(8)

        apps['app2_1'].set_virtual_link([apps['app3_1']]).set_frame(8)
        apps['app2_2'].set_virtual_link([apps['app2_3']]).set_frame(8)
        apps['app2_3'].set_virtual_link([apps['app1_3']]).set_frame(8).depend_on(apps['app2_2'])

        apps['app3_1'].set_virtual_link([apps['app3_2']]).set_frame(8).depend_on(apps['app2_1'])
        apps['app3_3'].set_virtual_link([apps['app1_1']]).set_frame(8)

        sc = model.Scheduler(network)
        sc.add_apps(list(apps.values()))

        hook = constrains.Z3Hook()
        sc.add_constrains(hook)
        df = hook.to_dataframe()
        an = analyzer.Analyzer(df, network.graph, sc.app_lcm)
        an.animate()


if __name__ == "__main__":
    unittest.main()
