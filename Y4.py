import json
import math
import matplotlib.pyplot as plt
import networkx as nx  # Thêm thư viện networkx để vẽ đồ thị chuyên nghiệp hơn


class Cluster:
    def __init__(self, node):
        self.nodes = {node['id']: node}
        self.weight = node.get('weight', 1)
        self.id = node['id']  # ID của cluster
        self.root = node['id']  # Root node của cluster
        self.max_hop = 1  # Hop count tối đa trong cluster

    def merge(self, other, new_root, hop_increment):
        self.nodes.update(other.nodes)
        self.weight += other.weight

        # Cập nhật hop count cho tất cả các nút trong cluster được gộp
        for node_id in other.nodes:
            self.nodes[node_id]['hop_count'] += hop_increment

        # Cập nhật max hop
        self.max_hop = max(self.max_hop, other.max_hop + hop_increment)
        self.root = new_root


def euclidean_distance(n1, n2):
    return math.sqrt((n1['x'] - n2['x']) ** 2 + (n1['y'] - n2['y']) ** 2)


def build_access_tree(backbone, access_nodes, W, max_hop=4):
    # Tạo từ điển nút và thêm thông tin hop_count
    nodes = {node['id']: node for node in [backbone] + access_nodes}
    hub_id = backbone['id']

    # Khởi tạo hop_count cho các nút
    for node in nodes.values():
        if node['id'] == hub_id:
            node['hop_count'] = 0  # Backbone có hop_count = 0
        else:
            node['hop_count'] = 1  # Các nút khác ban đầu hop_count = 1

    # Tạo clusters
    clusters = {nid: Cluster(nodes[nid]) for nid in nodes if nid != hub_id}
    parent = {nid: hub_id for nid in clusters}  # ban đầu nối trực tiếp hub
    active_nodes = set(clusters.keys())

    # Hàm tìm root cluster của một nút
    def find_cluster_root(nid):
        current = nid
        while clusters[current].root != current:
            clusters[current].root = clusters[clusters[current].root].root  # Path compression
            current = clusters[current].root
        return current

    # Hàm gộp cluster
    def union_clusters(i, j):
        root_i = find_cluster_root(i)
        root_j = find_cluster_root(j)

        if root_i == root_j:
            return False

        # Tính hop_increment
        hop_increment = (nodes[j]['hop_count'] + 1) - nodes[i]['hop_count']

        # Gộp cluster_i vào cluster_j
        clusters[root_j].merge(clusters[root_i], root_j, hop_increment)
        clusters[root_i].root = root_j  # Bổ sung dòng này để cập nhật root

        # Cập nhật parent
        parent[i] = j

        return True

    # Tính toán tradeoff
    def compute_tradeoff(i):
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
            tradeoff_val = euclidean_distance(nodes[i], nodes[hub_id]) - dist_i_j

            if tradeoff_val > 0:
                # Tính toán hop count mới nếu kết nối
                new_hop = nodes[j]['hop_count'] + 1
                new_max_hop = max(clusters[root_j].max_hop,
                                  clusters[root_i].max_hop + (new_hop - nodes[root_i]['hop_count']))

                if new_max_hop <= max_hop:
                    new_weight = clusters[root_i].weight + clusters[root_j].weight
                    if new_weight <= W and tradeoff_val > best_tradeoff:
                        best_tradeoff = tradeoff_val
                        best_j = j

        return (best_tradeoff, best_j) if best_j else (None, None)

    tradeoffs = {nid: compute_tradeoff(nid) for nid in active_nodes}
    edges = []

    while True:
        candidates = [(v[0], i, v[1]) for i, v in tradeoffs.items() if v[0] is not None]
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

        # Tính toán lại ràng buộc hop count
        new_hop = nodes[j]['hop_count'] + 1
        hop_increment = new_hop - nodes[root_i]['hop_count']
        new_max_hop = max(clusters[root_j].max_hop, clusters[root_i].max_hop + hop_increment)

        if new_max_hop > max_hop:
            tradeoffs[i] = (None, None)
            continue

        new_weight = clusters[root_i].weight + clusters[root_j].weight
        if new_weight > W:
            tradeoffs[i] = (None, None)
            continue

        # Thực hiện kết nối
        dist = euclidean_distance(nodes[i], nodes[j])
        edges.append((i, j, dist))
        union_clusters(i, j)

        # Cập nhật active nodes và tradeoffs
        active_nodes.remove(i)
        tradeoffs[i] = (None, None)
        tradeoffs[j] = compute_tradeoff(j)

    # Kết nối các cluster root về backbone
    connected_roots = set()
    for nid in clusters:
        root = find_cluster_root(nid)
        if root not in connected_roots:
            dist = euclidean_distance(nodes[root], nodes[hub_id])
            edges.append((root, hub_id, dist))
            connected_roots.add(root)
            parent[root] = hub_id

    total_cost = sum(e[2] for e in edges)
    hop_count = {nid: nodes[nid]['hop_count'] for nid in nodes if nid != hub_id}
    return total_cost, edges, parent, nodes, hop_count


def draw_access_tree(nodes, edges, hop_count, hub_id, max_hop=4):
    G = nx.Graph()
    pos = {}
    node_colors = []
    labels = {}

    # Thêm các node và xác định vị trí
    for node_id, node in nodes.items():
        G.add_node(node_id)
        pos[node_id] = (node['x'], node['y'])

        if node_id == hub_id:
            node_colors.append('red')
            labels[node_id] = f"Hub {node_id}"
        else:
            hop = hop_count.get(node_id, '?')
            labels[node_id] = f"{node_id} (h={hop})"
            if hop <= max_hop:
                node_colors.append('lightgreen')
            else:
                node_colors.append('salmon')

    # Thêm các cạnh
    for src, dst, cost in edges:
        G.add_edge(src, dst, weight=round(cost, 2))

    # Vẽ đồ thị
    plt.figure(figsize=(10, 8))
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=500)
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=9)

    # Vẽ các cạnh với nhãn chi phí
    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edges(G, pos, width=1.5, alpha=0.7, edge_color='gray')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)

    plt.title(f"Cây truy nhập (giới hạn hop = {max_hop})")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.grid(True)
    plt.axis('equal')
    plt.show()


def run_esau_williams_with_hop_limit(filename, W=15, max_hop=4):
    with open(filename, "r", encoding="utf-8") as f:
        mentor_groups = json.load(f)

    for i, group in enumerate(mentor_groups, 1):
        backbone = group['backbone']
        access_nodes = group['access_nodes']

        if len(access_nodes) == 0:
            print(f"Nhóm {i}: Không có access nodes, bỏ qua.")
            continue

        try:
            total_cost, edges, parent, nodes, hop_count = build_access_tree(
                backbone, access_nodes, W, max_hop
            )

            print(f"\nNhóm {i}: Backbone={backbone['id']}, Tổng chi phí = {round(total_cost, 2)}")
            sorted_edges = sorted(edges, key=lambda e: (e[1], e[0]))
            for e in sorted_edges:
                print(f"    {e[0]} -> {e[1]} (Chi phí={round(e[2], 2)}, Hop={nodes[e[0]]['hop_count']})")

            draw_access_tree(nodes, edges, hop_count, backbone['id'], max_hop)
        except Exception as e:
            print(f"Lỗi khi xử lý nhóm {i}: {str(e)}")
            continue

# Gọi chạy ví dụ:
run_esau_williams_with_hop_limit("mentor_groups.json", W=15, max_hop=4)