import networkx as nx
from antlr4 import *
from matplotlib import pyplot as plt

from Sqlparser.MySqlLexer import MySqlLexer
from Sqlparser.MySqlParser import MySqlParser
import pygraphviz as pgv

class ZrclAstNode:
    def __init__(self, name, node_id, parent=None, children=None):
        if children is None:
            children = []
        self.name = name      # 节点的内容
        self.node_id = node_id  # 节点的 ID
        self.parent = parent
        self.children = children

def parser_sql(sql_input):
    input_stream = InputStream(sql_input)
    lexer = MySqlLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = MySqlParser(stream)
    tree = parser.sqlStatement()  # 生成解析树
    return tree, parser

def build_sub_tree(antlr_ast_tree, parser, node_counter):
    if antlr_ast_tree.getChildCount() == 0:  # 叶子节点
        node_text = antlr_ast_tree.getText()
    else:  # 非叶子节点
        node_text = parser.ruleNames[antlr_ast_tree.getRuleIndex()]

    sub_tree_root = ZrclAstNode(node_text, node_counter[0])
    node_counter[0] += 1  # 递增节点 ID

    # 递归遍历子节点
    for i in range(antlr_ast_tree.getChildCount()):
        child = antlr_ast_tree.getChild(i)
        child_sub_tree = build_sub_tree(child, parser, node_counter)  # 递归构建子树
        sub_tree_root.children.append(child_sub_tree)  # 将子树添加到当前节点的子节点中

    return sub_tree_root  # 返回构建的子树根节点

def add_edges(graph, node):
    # 为当前节点添加边
    for child in node.children:
        G.add_node(child.node_id, label=child.name)
        graph.add_edge(node.node_id, child.node_id)  # 使用 ID 添加边
        add_edges(graph, child)  # 递归添加子节点的边

def extract_labels(node):
    """递归提取节点标签"""
    labels = {f'{node.node_id}': node.name}
    for child in node.children:
        labels.update(extract_labels(child))  # 合并子节点标签
    return labels

# SQL 输入
sqls = []
sqls.append("""SELECT * FROM c""")
sqls.append("""SELECT * FROM b""")
sub_trees = []
sub_parsers = []

#循环解析
for sql in sqls:
    tree, my_parser = parser_sql(sql)
    sub_trees.append(tree)
    sub_parsers.append(my_parser)

# 初始化节点计数器
node_counter = [0]  # 使用列表来保存计数器，以便在递归中修改

sub_tree_root = build_sub_tree(tree, my_parser, node_counter)

# 创建一个有向树
G = pgv.AGraph(directed=True)

# 添加树的节点和有向边
G.add_node(sub_tree_root.node_id, label=sub_tree_root.name)  # 添加根节点，使用 ID 作为节点标识
add_edges(G, sub_tree_root)  # 递归添加边

# 添加其他节点的 ID 和内容
def add_nodes(graph, node):
    # 添加当前节点
    graph.add_node(node.node_id, label=node.name)  # 使用 ID 作为节点标识
    for child in node.children:
        add_nodes(graph, child)  # 递归添加子节点

add_nodes(G, sub_tree_root)  # 添加所有节点

# 转换为 networkx 图
nx_tree = nx.nx_agraph.from_agraph(G)

# 使用层次布局（类似树的布局）
pos = nx.drawing.nx_agraph.graphviz_layout(nx_tree, prog='dot')

labels = extract_labels(sub_tree_root)  # 获取整个树的标签
# 绘制层次树
plt.figure(figsize=(8, 10))

# 绘制文本框而不是圆点
for node_id in nx_tree.nodes:
    x, y = pos[node_id]
    plt.text(x, y, labels[node_id], fontsize=12, ha='center', bbox=dict(facecolor='pink', edgecolor='black', boxstyle='round,pad=0.3'))

plt.axis('off')
nx.draw_networkx_edges(nx_tree, pos)
plt.title("Tree Visualization with Hierarchical Layout", fontsize=18)
plt.show()
