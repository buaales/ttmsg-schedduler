import networkx
import networkx.generators as ntx_gen
import random
import sys
from msg_scheduler import model, constrains, analyzer


def test_topo():
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


def test_director():
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
    an = analyzer.Analyzer(df, network, sc.app_lcm)
    an.print_by_time()


def test_simple():
    network: model.Network = model.Network()
    msg_node1 = model.SwitchNode(f'msg_core1')
    msg_node2 = model.SwitchNode(f'msg_core2')
    app_node1 = model.EndNode('app_core1')
    app_node2 = model.EndNode('app_core2')

    network.add_node(msg_node1)
    network.add_node(msg_node2)
    network.add_node(app_node1)
    network.add_node(app_node2)

    network.add_link(app_node1.name, msg_node1.name)
    network.add_link(app_node2.name, msg_node2.name)
    network.add_link(msg_node1.name, msg_node2.name)

    app1 = model.Application(network, 'app1', 'app_core1')
    app2 = model.Application(network, 'app2', 'app_core2')

    app1.set_virtual_link([app2]).set_frame(6)
    app2.set_virtual_link([app1]).set_frame(6).depend_on(app1)

    sc = model.Scheduler(network)
    sc.add_apps([app1, app2])

    hook = constrains.Z3Hook()
    sc.add_constrains(hook)

    df = hook.to_dataframe()
    an = analyzer.Analyzer(df, network, sc.app_lcm)
    an.print_by_time()
    an.animate()


def test_paper():
    network: model.Network = model.Network()
    # 创建多核处理器
    for proc_idx in range(1, 4):
        msg_node = model.SwitchNode(f'msg_core_{proc_idx}')
        network.add_node(msg_node)

        app_nodes = [model.EndNode(f'app_core_{proc_idx}_{core_idx}') for core_idx in range(1, 4)]
        for n in app_nodes:
            network.add_node(n)
            network.add_link(msg_node.name, n.name)

    switch = model.SwitchNode('msg_switch', 1)
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

    apps['app2_1'].set_virtual_link([apps['app1_1']]).set_frame(8)
    apps['app2_2'].set_virtual_link([apps['app2_1']]).set_frame(8).depend_on(apps['app1_2'])
    apps['app2_3'].set_virtual_link([apps['app3_3'], apps['app3_2']]).set_frame(8)

    apps['app3_1'].set_virtual_link([apps['app3_2']]).set_frame(8).depend_on(apps['app1_2'])
    apps['app3_2'].set_virtual_link([apps['app3_3']]).set_frame(4)
    apps['app3_3'].set_virtual_link([apps['app1_1']]).set_frame(8)

    sc = model.Scheduler(network)
    sc.add_apps(list(apps.values()))

    hook = constrains.Z3Hook()
    sc.add_constrains(hook)
    hook.print()
    df = hook.to_dataframe()
    an = analyzer.Analyzer(df, network, sc.app_lcm)
    an.print_by_time()
    an.animate()
    an.export(('192.168.11.224', '192.168.11.209'))
    return


def test_random():
    g: networkx.Graph = ntx_gen.random_tree(random.randint(5, 20), seed=random.randint(1, 99999999))
    network: model.Network = model.Network()
    node_name_map = {}
    for n in g.nodes():
        nei = list(g.neighbors(n))
        if len(nei) == 1:
            new_node = model.EndNode(f'app_{n}')
        else:
            new_node = model.SwitchNode(f'msg_{n}')
        network.add_node(new_node)
        node_name_map[n] = new_node.name
    for e in g.edges:
        network.add_link(node_name_map[e[0]], node_name_map[e[1]])

    # 生成app
    apps = set()
    for en in network.end_nodes:
        app = model.Application(network, f'{en.name}', en.name)
        apps.add(app)

    for app in apps:
        target_apps = random.sample(apps, random.randint(1, max(2, len(network.end_nodes) // 2)))
        if app in target_apps:
            target_apps.remove(app)
        app.set_virtual_link(list(target_apps)).set_frame(int(len(apps) * 1.5))

    sc = model.Scheduler(network)
    sc.add_apps(list(apps))

    hook = constrains.Z3Hook()
    sc.add_constrains(hook)
    hook.print()
    if hook.solve() is None:
        test_random()
        return
    df = hook.to_dataframe()
    an = analyzer.Analyzer(df, network, sc.app_lcm)
    an.print_by_time()
    an.animate()


if __name__ == '__main__':
    for arg in sys.argv[1:]:
        eval(f'test_{arg}()')
