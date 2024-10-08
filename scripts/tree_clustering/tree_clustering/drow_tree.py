import matplotlib.pyplot as plt
import networkx as nx
from anytree import Node, RenderTree

def parse_sql_string(sql_string):
    stack = []
    current_node = None
    node_count = {}

    tokens = sql_string.replace('(', ' ( ').replace(')', ' ) ').split()

    for token in tokens:
        if token == '(':
            if current_node is not None:
                stack.append(current_node)
        elif token == ')':
            if stack:
                current_node = stack.pop()
        else:
            # 使用计数器跟踪每个节点的出现次数
            if token not in node_count:
                node_count[token] = 0
            node_count[token] += 1
            unique_name = f"{token}_{node_count[token]}"  # 生成唯一名称

            if current_node is None:
                current_node = Node(unique_name)  # 创建根节点
            else:
                new_node = Node(unique_name, parent=current_node)  # 创建子节点
                current_node = new_node

    return current_node

def build_graph(node, graph):
    for child in node.children:
        graph.add_edge(node.name, child.name)  # 使用生成的唯一名称
        build_graph(child, graph)

def plot_tree(root):
    graph = nx.DiGraph()
    build_graph(root, graph)

    pos = nx.nx_agraph.graphviz_layout(graph, prog='dot', args='-Gnodesep=0.5 -Granksep=0.75')

    plt.figure(figsize=(12, 8))  # 调整图形大小
    nx.draw(graph, pos, with_labels=True, arrows=True,
            node_size=0, font_size=10, edge_color='black', font_color='black',
            bbox=dict(facecolor='white', edgecolor='black', boxstyle='round,pad=0.3'))
    plt.title("SQL Statements Tree Structure")
    plt.axis('off')  # 关闭坐标轴
    plt.show()

# 输入新的 SQL 字符串
sql_string = "(sqlStatement (ddlStatement (createTable CREATE TABLE (tableName (fullId (uid (simpleId v0)))) (createDefinitions ( (createDefinition (fullColumnName (uid (simpleId v2))) (columnDefinition (dataType DOUBLE) (columnConstraint PRIMARY KEY))) )))))"

# 解析并构建树
root = parse_sql_string(sql_string)

# 绘制树结构
if root:
    plot_tree(root)
else:
    print("No nodes were created.")
