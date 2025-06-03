import json
import math
import matplotlib.pyplot as plt
import networkx as nx  # Thêm thư viện networkx để vẽ đồ thị


class Cluster:
    def __init__(self, node):
        self.nodes = {node['id']: node}
        self.weight = node.get('weight', 1)
        self.id = node['id']  # Thêm ID cho cluster
        self.root = node['id']  # Root của cluster

    def merge(self, other):
        self.nodes.update(other.nodes)
        self.weight += other.weight
        # Cập nhật root mới khi gộp cluster
        for node_id in other.nodes:
            if node_id != self.id:
                self.nodes[node_id]['cluster_root'] = self.root


def euclidean_distance(n1, n2):
    return math.sqrt((n1['x'] - n2['x']) ** 2 + (n1['y'] - n2['y']) ** 2)


def build_access_tree(backbone, access_nodes, W):
    nodes = {node['id']: node for node in [backbone] + access_nodes}
    hub_id = backbone['id']

    # Thêm thông tin cluster_root cho mỗi node
    for node_id, node in nodes.items():
        node['cluster_root'] = node_id

    clusters = {nid: Cluster(nodes[nid]) for nid in nodes if nid != hub_id}
    parent = {nid: hub_id for nid in clusters}  # ban đầu nối trực tiếp hub
    active_nodes = set(clusters.keys())
    cost_i_hub = {nid: euclidean_distance(nodes[nid], backbone) for nid in clusters}

    def find_cluster_root(nid):
        return nodes[nid]['cluster_root']

    def union_clusters(i, j):
        """Gộp cluster chứa i vào cluster chứa j"""
        root_i = find_cluster_root(i)
        root_j = find_cluster_root(j)

        if root_i == root_j:
            return False

        # Gộp cluster i vào cluster j
        clusters[root_j].merge(clusters[root_i])
        del clusters[root_i]

        # Cập nhật root cho tất cả các node trong cluster cũ
        for node_id in clusters[root_j].nodes:
            nodes[node_id]['cluster_root'] = root_j

        return True

    def compute_tradeoff(i, active_nodes):
        best_tradeoff = -math.inf
        best_j = None
        root_i = find_cluster_root(i)

        for j in active_nodes:
            if j == i:
                continue

            root_j = find_cluster_root(j)
            if root_i == root_j:
                continue

            dist_i_j = euclidean_distance(nodes[i], nodes[j])
            tradeoff_val = cost_i_hub[i] - dist_i_j

            if tradeoff_val > 0:
                new_weight = clusters[root_i].weight + clusters[root_j].weight
                if new_weight <= W and tradeoff_val > best_tradeoff:
                    best_tradeoff = tradeoff_val
                    best_j = j

        if best_j is None:
            return None, None
        return best_tradeoff, best_j

    tradeoffs = {nid: compute_tradeoff(nid, active_nodes) for nid in active_nodes}
    edges = []

    while True:
        candidates = []
        for nid in active_nodes:
            if tradeoffs[nid][0] is not None:
                candidates.append((tradeoffs[nid][0], nid, tradeoffs[nid][1]))

        if not candidates:
            break

        max_tradeoff, i, j = max(candidates, key=lambda x: x[0])

        if max_tradeoff <= 0:
            break

        root_i = find_cluster_root(i)
        root_j = find_cluster_root(j)

        if root_i == root_j:
            tradeoffs[i] = (None, None)
            continue

        new_weight = clusters[root_i].weight + clusters[root_j].weight
        if new_weight > W:
            tradeoffs[i] = (None, None)
            continue

        # Thực hiện gộp cluster
        if not union_clusters(i, j):
            tradeoffs[i] = (None, None)
            continue

        # Cập nhật parent
        parent[i] = j
        dist = euclidean_distance(nodes[i], nodes[j])
        edges.append((i, j, dist))

        # Cập nhật active nodes và tradeoffs
        active_nodes.remove(i)
        tradeoffs[i] = (None, None)
        tradeoffs[j] = compute_tradeoff(j, active_nodes)

    # Kết nối các cluster còn lại trực tiếp vào backbone
    for root_id, cluster in clusters.items():
        if root_id in active_nodes:
            dist = cost_i_hub[root_id]
            edges.append((root_id, hub_id, dist))
            parent[root_id] = hub_id

    total_cost = sum(e[2] for e in edges)
    return total_cost, edges, parent, nodes


def plot_tree(edges, nodes, hub_id):
    G = nx.DiGraph()
    pos = {nid: (node['x'], node['y']) for nid, node in nodes.items()}

    # Thêm node vào đồ thị với thuộc tính màu
    for nid, node in nodes.items():
        G.add_node(nid)

    # Thêm các cạnh vào đồ thị
    for src, dst, cost in edges:
        G.add_edge(src, dst, weight=round(cost, 2))

    plt.figure(figsize=(10, 8))
    ax = plt.gca()
    ax.set_title("Cây truy nhập Esau-Williams", fontsize=14, fontweight='bold')
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.grid(True, linestyle='--', alpha=0.5)

    # Màu và kích cỡ node
    node_colors = ['red' if nid == hub_id else 'skyblue' for nid in G.nodes()]
    node_sizes = [200 if nid == hub_id else 200 for nid in G.nodes()]
    node_border_colors = ['black' if nid == hub_id else 'gray' for nid in G.nodes()]

    # Vẽ nodes
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, edgecolors=node_border_colors, linewidths=1.5)
    nx.draw_networkx_labels(G, pos, font_size=9, font_weight='bold')

    # Vẽ edges
    nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=False, width=2, alpha=0.7)

    # Vẽ trọng số cạnh
    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)

    plt.tight_layout()
    plt.show()



def run_esau_williams(filename, W=15):
    with open(filename, "r", encoding="utf-8") as f:
        mentor_groups = json.load(f)

    for i, group in enumerate(mentor_groups, 1):
        backbone = group['backbone']
        access_nodes = group['access_nodes']

        if len(access_nodes) == 0:
            print(f"Nhóm {i}: Không có access nodes, bỏ qua.")
            continue

        total_cost, edges, parent, nodes = build_access_tree(backbone, access_nodes, W)

        # Sắp xếp edges để in ra theo thứ tự dễ đọc
        sorted_edges = sorted(edges, key=lambda e: (e[1], e[0]))

        print(f"\nNhóm {i}: Backbone={backbone['id']}, Tổng chi phí = {round(total_cost, 2)}")
        for e in sorted_edges:
            print(f"    {e[1]} -> {e[0]} (Chi phí={round(e[2], 2)})")

        plot_tree(edges, nodes, backbone['id'])


# Ví dụ chạy:
run_esau_williams("mentor_groups.json", W=15)