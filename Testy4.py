import json
import math
import matplotlib.pyplot as plt
import networkx as nx


# --- Định nghĩa Cluster để lưu thông tin mỗi “cụm” (cluster) --- #
class Cluster:
    def __init__(self, node):
        # nodes là dict {node_id: node_dict}, chứa toàn bộ node trong cụm
        self.nodes = {node['id']: node}
        # weight = tổng weight của tất cả node trong cụm
        self.weight = node.get('weight', 1)
        # max_hop = hop count lớn nhất trong cụm (so với backbone) trước khi gộp
        self.max_hop = 1

    def merge(self, other, hop_increment, nodes_global):
        """
        Gộp cụm 'other' vào self, kèm theo:
        - hop_increment: số hop phải tăng cho từng node của other
        - nodes_global: reference tới dict chứa hop_count của từng node (để cập nhật)
        """
        # 1) Gộp đựng tất cả node từ other vào self
        self.nodes.update(other.nodes)
        # 2) Cộng trọng số
        self.weight += other.weight
        # 3) Cập nhật hop_count cho từng node trong other
        for node_id in other.nodes:
            nodes_global[node_id]['hop_count'] += hop_increment
        # 4) Cập nhật lại max_hop của cụm gộp (bằng max giữa chính max_hop và other.max_hop + hop_increment)
        self.max_hop = max(self.max_hop, other.max_hop + hop_increment)


# --- Hàm tính khoảng cách Euclidean giữa hai node --- #
def euclidean_distance(n1, n2):
    return math.hypot(n1['x'] - n2['x'], n1['y'] - n2['y'])


# --- Xây dựng “cây truy nhập” với thuật toán Esau-Williams + giới hạn hop --- #
def build_access_tree(backbone, access_nodes, W, max_hop=4):
    """
    backbone: dict {id, x, y, weight}
    access_nodes: list of dicts mỗi dict {id, x, y, weight}
    W: ngưỡng tổng trọng số (max total weight khi gộp)
    max_hop: giới hạn hop count tối đa so với backbone

    Trả về:
    - total_cost: tổng chi phí (sum of Euclidean edges)
    - edges: list of (src, dst, distance)
    - parent: dict mapping mỗi node => parent (ít dùng nhưng in ra)
    - nodes: dict tất cả node kèm hop_count cuối cùng
    - hop_count: dict {node_id: hop_count}
    """

    # 1) Khởi tạo hoán vị cho tất cả node
    nodes = {node['id']: dict(node) for node in [backbone] + access_nodes}
    hub_id = backbone['id']

    # 2) Thiết lập hop_count ban đầu:
    #    - backbone (hub) hop_count = 0
    #    - mọi access node hop_count = 1
    for node in nodes.values():
        node['hop_count'] = 0 if node['id'] == hub_id else 1

    # 3) Khởi tạo Union-Find (parent_uf) chỉ cho access_nodes
    parent_uf = {node['id']: node['id'] for node in access_nodes}
    def find_uf(x):
        # Tìm “root” (leader) với path compression
        while parent_uf[x] != x:
            parent_uf[x] = parent_uf[parent_uf[x]]
            x = parent_uf[x]
        return x

    # 4) Khởi tạo Cluster cho mỗi access node (ban đầu mỗi node là 1 cụm)
    clusters = {node['id']: Cluster(node) for node in access_nodes}
    # active_roots: tập các IDs hiện đang là root của một cluster
    active_roots = set(clusters.keys())

    # parent dict chỉ để in ra kết quả, mapping “mỗi root cũ” → nơi nó gộp vào
    parent = {nid: hub_id for nid in clusters}

    # edges: danh sách (src, dst, distance) sẽ trả ra
    edges = []

    # 5) Hàm gộp cụm i vào cụm j
    def union_clusters(i, j):
        root_i = find_uf(i)
        root_j = find_uf(j)
        if root_i == root_j:
            return False

        # a) Tính hop_increment: hop_j_before + 1 - hop_i_before
        hop_i_before = nodes[root_i]['hop_count']
        hop_j_before = nodes[j]['hop_count']
        hop_increment = (hop_j_before + 1) - hop_i_before

        # b) Gộp cluster root_i vào root_j
        clusters[root_j].merge(clusters[root_i], hop_increment, nodes)
        # c) Cập nhật hop_count cho chính root_i (sau khi merge)
        nodes[root_i]['hop_count'] += hop_increment

        # d) Union-Find union
        parent_uf[root_i] = root_j

        # e) Xóa cụm root_i khỏi clusters (vì root_i giờ đã thuộc root_j)
        del clusters[root_i]
        active_roots.discard(root_i)

        # f) Cập nhật parent map
        parent[root_i] = root_j

        return True

    # 6) Tính tradeoff cho một node i (i phải là “active root” hoặc bản thân i là một node chưa gộp)
    def compute_tradeoff(i):
        root_i = find_uf(i)
        # Nếu root_i không còn là key trong clusters (đã từng gộp)
        if root_i not in clusters:
            return (None, None)

        best_t = -math.inf
        best_j = None
        curr_max_hop_i = clusters[root_i].max_hop
        weight_i = clusters[root_i].weight

        for j in list(active_roots):
            if j == i:
                continue
            root_j = find_uf(j)
            # Bỏ qua nếu root_j không còn tồn tại trong clusters hoặc bằng root_i
            if root_j not in clusters or root_j == root_i:
                continue

            # i → hub minus i → j
            dist_i_hub = euclidean_distance(nodes[i], nodes[hub_id])
            dist_i_j = euclidean_distance(nodes[i], nodes[j])
            tradeoff_val = dist_i_hub - dist_i_j
            if tradeoff_val <= 0:
                continue

            # Tính nếu gộp i vào j, hop mới cho cụm i là gì
            hop_i = nodes[root_i]['hop_count']
            hop_j = nodes[j]['hop_count']
            hop_inc = (hop_j + 1) - hop_i
            new_max_hop_i = curr_max_hop_i + hop_inc
            curr_max_hop_j = clusters[root_j].max_hop
            overall_max_hop = max(curr_max_hop_j, new_max_hop_i)

            # Kiểm ràng buộc hop ≤ max_hop và tổng weight ≤ W
            if overall_max_hop > max_hop:
                continue
            if weight_i + clusters[root_j].weight > W:
                continue

            if tradeoff_val > best_t:
                best_t = tradeoff_val
                best_j = j

        return (best_t, best_j) if best_j is not None else (None, None)

    # 7) Khởi tạo tradeoffs cho mỗi active root
    tradeoffs = {nid: compute_tradeoff(nid) for nid in active_roots}

    # 8) Vòng lặp chính: tìm cặp (i, j) có tradeoff lớn nhất để gộp
    while True:
        # a) Tập hợp các (tradeoff, i, j) hợp lệ
        candidates = [
            (tup[0], i, tup[1])
            for i, tup in tradeoffs.items()
            if tup[0] is not None and i in active_roots
        ]
        if not candidates:
            break
        # b) Lấy cặp có tradeoff lớn nhất
        max_t, i, j = max(candidates, key=lambda x: x[0])
        if max_t <= 0:
            break

        root_i = find_uf(i)
        root_j = find_uf(j)
        # Bỏ nếu cùng root hoặc không còn tồn tại
        if root_i == root_j or root_i not in clusters or root_j not in clusters:
            tradeoffs[i] = (None, None)
            continue

        # Kiểm ràng buộc lần cuối trước khi gộp
        hop_i = nodes[root_i]['hop_count']
        hop_j = nodes[j]['hop_count']
        hop_inc = (hop_j + 1) - hop_i
        new_max_hop_i = clusters[root_i].max_hop + hop_inc
        curr_max_hop_j = clusters[root_j].max_hop
        if max(curr_max_hop_j, new_max_hop_i) > max_hop:
            tradeoffs[i] = (None, None)
            continue
        if clusters[root_i].weight + clusters[root_j].weight > W:
            tradeoffs[i] = (None, None)
            continue

        # Thực hiện nối i → j
        dist = euclidean_distance(nodes[i], nodes[j])
        edges.append((i, j, dist))

        # Gộp cluster
        union_clusters(i, j)

        # Cập nhật lại tradeoffs
        tradeoffs[i] = (None, None)
        tradeoffs[j] = compute_tradeoff(j)

    # 9) Cuối cùng, nối tất cả “root còn lại” (active_roots) về backbone
    connected_roots = set()
    for root in list(clusters.keys()):
        # Đảm bảo root vẫn là leader của chính nó
        if find_uf(root) != root:
            continue
        # Nối root → hub
        dist_hub = euclidean_distance(nodes[root], nodes[hub_id])
        edges.append((root, hub_id, dist_hub))
        parent[root] = hub_id
        connected_roots.add(root)

    # 10) Tính lại hop_count bằng BFS (đảm bảo chính xác)
    G = nx.Graph()
    for src, dst, _ in edges:
        G.add_edge(src, dst)
    if hub_id in G:
        # Nếu hub có trong graph
        hops = nx.single_source_shortest_path_length(G, hub_id)
        for nid, h in hops.items():
            if nid in nodes:
                nodes[nid]['hop_count'] = h
    else:
        # Không có cạnh nào nối về hub
        for nid in nodes:
            nodes[nid]['hop_count'] = 0 if nid == hub_id else float('inf')

    total_cost = sum(e[2] for e in edges)
    hop_count = {nid: nodes[nid]['hop_count'] for nid in nodes if nid != hub_id}
    return total_cost, edges, parent, nodes, hop_count


# --- Hàm vẽ “cây truy nhập” sau khi tính toán --- #
def draw_access_tree(nodes, edges, hop_count, hub_id, max_hop=4):
    G = nx.Graph()
    pos = {}
    node_colors = []
    labels = {}

    for node_id, node in nodes.items():
        G.add_node(node_id)
        pos[node_id] = (node['x'], node['y'])
        if node_id == hub_id:
            node_colors.append('red')
            labels[node_id] = f"Hub {node_id}"
        else:
            hop = hop_count.get(node_id, '?')
            labels[node_id] = f"{node_id} (h={hop})"
            node_colors.append('lightgreen' if hop <= max_hop else 'salmon')

    for src, dst, cost in edges:
        G.add_edge(src, dst, weight=round(cost, 2))

    plt.figure(figsize=(8, 6))
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=500)
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=9)
    nx.draw_networkx_edges(G, pos, width=1.5, alpha=0.7, edge_color='gray')
    edge_labels = nx.get_edge_attributes(G, 'weight')
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=8)

    plt.title(f"Cây truy nhập (giới hạn hop = {max_hop})")
    plt.xlabel("X"); plt.ylabel("Y")
    plt.axis('equal'); plt.grid(True)
    plt.show()


# --- Hàm chính: đọc file JSON, duyệt qua từng group, in kết quả và vẽ đồ thị --- #
def run_esau_williams_with_hop_limit(filename, W=15, max_hop=4):
    with open(filename, "r", encoding="utf-8") as f:
        mentor_groups = json.load(f)

    for i, group in enumerate(mentor_groups, 1):
        backbone = group['backbone']
        access_nodes = group['access_nodes']

        if not access_nodes:
            print(f"Nhóm {i}: Không có access nodes, bỏ qua.")
            continue

        print(f"\n--- Xử lý Nhóm {i}: Backbone={backbone['id']}, Số access nodes={len(access_nodes)} ---")
        try:
            total_cost, edges, parent, nodes, hop_count = build_access_tree(
                backbone, access_nodes, W, max_hop
            )

            # In kết quả
            print(f"  Tổng chi phí = {round(total_cost, 2)}")
            for src, dst, cost in sorted(edges, key=lambda e: (e[1], e[0])):
                print(f"    {src} -> {dst}  (Chi phí={round(cost, 2)}, Hop={nodes[src]['hop_count']})")

            # Kiểm tra có node nào vi phạm hop không
            violations = [nid for nid, h in hop_count.items() if h > max_hop]
            if violations:
                print(f"  CẢNH BÁO: Các node sau vi phạm hop count (>{max_hop}): {violations}")

            # Kiểm tra node nào chưa kết nối (nếu có)
            connected = set([backbone['id']])
            for src, dst, _ in edges:
                connected.add(src); connected.add(dst)
            disconnected = [nid for nid in nodes if nid not in connected]
            if disconnected:
                print(f"  CẢNH BÁO: Các node sau chưa được kết nối: {disconnected}")

            # Vẽ đồ thị
            draw_access_tree(nodes, edges, hop_count, backbone['id'], max_hop)

        except Exception as e:
            import traceback
            print(f"Lỗi khi xử lý Nhóm {i}: {e}")
            traceback.print_exc()
            continue


# --- CHẠY THẬT với file mentor_groups.json --- #
if __name__ == "__main__":
    run_esau_williams_with_hop_limit("mentor_groups.json", W=15, max_hop=2)
