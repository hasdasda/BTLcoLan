
import random
import math
import matplotlib.pyplot as plt

num_inf = math.inf
num_ninf = -math.inf

# ---------------------------
# LOP NODE
# ---------------------------
class Node:
    def __init__(self):
        self.name = 0
        self.x = 0
        self.y = 0
        self.traffic = 0
        self.weight = 0
        self.awardPoint = 0
        self.distanceToCenter = 0

        self.weight_ew = 0
        self.weight_of_group = 0
        self.group_node_to_center = 0
        self.thoa_hiep = num_ninf
        self.cost_to_center = num_inf
        self.next_connect = 0
        self.group_size = 1
        self.ListConnect = []

    def create_name(self, name):
        self.name = name
        self.group_node_to_center = name

    def set_position(self, x, y):
        self.x = round(x,2)
        self.y = round(y,2)

    def get_name(self): return self.name
    def get_position_x(self): return self.x
    def get_position_y(self): return self.y
    def get_weight(self): return self.weight
    def get_list_connect(self): return self.ListConnect
    def get_thoahiep(self): return self.thoa_hiep
    def get_next_connect(self): return self.next_connect
    def get_group_node_to_center(self): return self.group_node_to_center
    def get_weight_of_group(self): return self.weight_of_group
    def get_group_size(self): return self.group_size
    def get_cost_to_center(self): return self.cost_to_center

    def set_cost_to_center(self, c): self.cost_to_center = c
    def set_next_connect(self, index): self.next_connect = index
    def set_thoahiep(self, t): self.thoa_hiep = t
    def set_group_node_to_center(self, index): self.group_node_to_center = index
    def set_weight_of_group(self, w): self.weight_of_group = w
    def set_group_size(self, s): self.group_size = s

    def set_connect(self, i): self.ListConnect.append(i)
    def reset_list_connect(self): self.ListConnect.clear()

    def set_weight(self, w):
        self.weight = w
        self.weight_of_group = w

# ---------------------------
# KHOI TAO DANH SACH NODES THEO DE BAI
# ---------------------------
def initialize_nodes_de6(num_nodes=100, max_coord=1000):
    nodes = []
    special_weights = {
        3: 30, 12: 30, 69: 30, 29: 30,
        17: 6, 22: 6, 49: 6,
        77: 4, 63: 4, 6: 4,
        37: 5, 42: 5, 47: 5,
        57: 3, 45: 3, 8: 3
    }
    for i in range(1, num_nodes + 1):
        node = Node()
        node.create_name(i)
        x, y = random.randint(0, max_coord), random.randint(0, max_coord)
        node.set_position(x, y)
        node.set_weight(special_weights.get(i, 1))
        nodes.append(node)
    return nodes

# ---------------------------
# HAM TINH KHOANG CACH
# ---------------------------
def calc_distance_2Dpoint(a, b):
    return round(math.sqrt((a.get_position_x() - b.get_position_x())**2 + (a.get_position_y() - b.get_position_y())**2), 4)

# ---------------------------
# GIAI THUAT ESAU-WILLIAMS
# ---------------------------
def esau_williams_subtree(nodes, w_ew=15, hop_limit=4, debug=False):
    N = len(nodes)
    link_cost = [[num_inf]*N for _ in range(N)]

    for i in range(N):
        for j in range(i+1, N):
            c = calc_distance_2Dpoint(nodes[i], nodes[j])
            link_cost[i][j] = link_cost[j][i] = c

    center = nodes[68]
    for i in range(1, N):
        nodes[i].set_cost_to_center(link_cost[0][i])
        nodes[i].set_next_connect(0)
        nodes[i].set_thoahiep(num_inf)
        nodes[i].set_group_node_to_center(i)
        nodes[i].set_weight_of_group(nodes[i].get_weight())
        nodes[i].set_group_size(1)
        nodes[i].reset_list_connect()
        nodes[i].set_connect(center.get_name())

    center.set_group_node_to_center(center.get_name())
    center.set_weight_of_group(center.get_weight())
    center.set_group_size(1)
    center.reset_list_connect()

    def cap_nhat_thoa_hiep():
        for i in range(1, N):
            min_th = num_inf
            best_j = None
            for j in range(1, N):
                if nodes[i].get_group_node_to_center() == nodes[j].get_group_node_to_center():
                    continue
                th = link_cost[i][j] - nodes[i].get_cost_to_center()
                if th < min_th:
                    min_th = th
                    best_j = j
            nodes[i].set_thoahiep(min_th)
            nodes[i].set_next_connect(nodes[best_j].get_name())

    cap_nhat_thoa_hiep()

    while True:
        min_th = 0
        u_idx = -1
        for i in range(1, N):
            if nodes[i].get_thoahiep() < min_th:
                min_th = nodes[i].get_thoahiep()
                u_idx = i

        if u_idx == -1:
            break

        u = nodes[u_idx]
        v_name = u.get_next_connect()
        v_idx = next(idx for idx in range(N) if nodes[idx].get_name() == v_name)
        v = nodes[v_idx]

        total_w = u.get_weight_of_group() + v.get_weight_of_group()
        total_size = u.get_group_size() + v.get_group_size()

        if total_w <= w_ew and total_size <= hop_limit:
            u.reset_list_connect()
            u.set_connect(v.get_name())

            gid_src = u.get_group_node_to_center()
            gid_dst = v.get_group_node_to_center()

            for i in range(N):
                if nodes[i].get_group_node_to_center() == gid_src:
                    nodes[i].set_group_node_to_center(gid_dst)

            for i in range(N):
                if nodes[i].get_group_node_to_center() == gid_dst:
                    nodes[i].set_weight_of_group(total_w)
                    nodes[i].set_group_size(total_size)
                    nodes[i].set_cost_to_center(v.get_cost_to_center())
        else:
            link_cost[u_idx][v_idx] = link_cost[v_idx][u_idx] = num_inf

        cap_nhat_thoa_hiep()

    return nodes

# ---------------------------
# VE CAY ESAU-WILLIAMS
# ---------------------------
def draw_esau_tree(subnet_nodes, MAX):
    xpos = [n.get_position_x() for n in subnet_nodes]
    ypos = [n.get_position_y() for n in subnet_nodes]

    for node in subnet_nodes:
        plt.text(node.get_position_x(), node.get_position_y(), str(node.get_name()), fontsize=8,
                 bbox=dict(facecolor='yellow' if node == subnet_nodes[0] else 'white', edgecolor='black', boxstyle='round'))
        for conn_id in node.get_list_connect():
            conn_node = next(n for n in subnet_nodes if n.get_name() == conn_id)
            plt.plot([node.get_position_x(), conn_node.get_position_x()],
                     [node.get_position_y(), conn_node.get_position_y()], 'k-')

    plt.plot(xpos, ypos, 'ro')
    plt.title(f"Cay Esau-Williams: Backbone {subnet_nodes[0].get_name()}")
    plt.axis([-0.05*MAX, 1.05*MAX, -0.05*MAX, 1.05*MAX])
    plt.grid(True)
    plt.show()

# ---------------------------
# TINH CHI PHI CUA CAY
# ---------------------------
def calculate_total_cost(subnet_nodes):
    cost = 0
    for node in subnet_nodes:
        for conn in node.get_list_connect():
            target = next(n for n in subnet_nodes if n.get_name() == conn)
            cost += calc_distance_2Dpoint(node, target)
    return round(cost, 4)

if __name__ == "__main__":
    MAX = 1000
    W = 15      # Giới hạn trọng số nhóm
    H = 4       # Giới hạn số bước nhảy

    # Khởi tạo 1 subnet ví dụ với 1 backbone và một số node đầu cuối
    nodes = initialize_nodes_de6(num_nodes=100, max_coord=MAX)  # Dùng 10 node để dễ kiểm thử
    subnet = esau_williams_subtree(nodes, w_ew=W, hop_limit=H, debug=False)

    # Vẽ cây kết quả
    draw_esau_tree(subnet, MAX)

    # Tính chi phí
    print("Tổng chi phí cây truy nhập:", calculate_total_cost(subnet))
