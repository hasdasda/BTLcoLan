import random
import math
import matplotlib.pyplot as plt

# ==================== Cài đặt mặc định ====================
W_THRESHOLD = 2
RADIUS_RATIO = 0.3
C = 14
NUM_NODES = 100
MAX_COORD = 1000
OUTPUT_FILE = "mentor_output.txt"

# ==================== Lớp Node ====================
class Node:
    def __init__(self, id, x, y, weight):
        self.id = id
        self.x = x
        self.y = y
        self.weight = weight
        self.is_backbone = False

# ==================== Hàm tính toán ====================
def calculate_distance(n1, n2):
    return math.sqrt((n1.x - n2.x) ** 2 + (n1.y - n2.y) ** 2)

def calculate_max_distance(nodes):
    max_dist = 0
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            dist = calculate_distance(nodes[i], nodes[j])
            if dist > max_dist:
                max_dist = dist
    return max_dist

def calculate_award(node, center_x, center_y, max_dist, max_weight):
    dc = math.sqrt((node.x - center_x) ** 2 + (node.y - center_y) ** 2)
    norm_dist = (max_dist - dc) / max_dist if max_dist > 0 else 0
    norm_weight = node.weight / max_weight if max_weight > 0 else 0
    return 0.5 * norm_dist + 0.5 * norm_weight

# ==================== Khởi tạo mạng ====================
def initialize_network():
    nodes = []
    special_weights = {
        3: 30, 12: 30, 69: 30, 29: 30,
        17: 6, 22: 6, 49: 6,
        77: 4, 63: 4, 6: 4,
        37: 5, 42: 5, 47: 5,
        57: 3, 45: 3, 8: 3
    }
    for i in range(1, NUM_NODES + 1):
        x = random.randint(0, MAX_COORD)
        y = random.randint(0, MAX_COORD)
        weight = special_weights.get(i, 1)
        nodes.append(Node(i, x, y, weight))
    return nodes

# ==================== Gán access node ====================
def assign_access_nodes(all_nodes, backbones, threshold_distance, assigned_ids):
    access_map = {bb.id: [] for bb in backbones}

    for node in all_nodes:
        if node.id in assigned_ids:
            continue  # Đã được gán trước đó

        nearest_bb = None
        min_dist = float('inf')
        for bb in backbones:
            dist = calculate_distance(node, bb)
            if dist <= threshold_distance and dist < min_dist:
                min_dist = dist
                nearest_bb = bb

        if nearest_bb is not None:
            access_map[nearest_bb.id].append(node.id)
            assigned_ids.add(node.id)

    return access_map

# ==================== Chọn backbone ban đầu ====================
def find_initial_backbones(nodes):
    backbones = []
    for node in nodes:
        if node.weight / C > W_THRESHOLD:
            node.is_backbone = True
            backbones.append(node)
    return backbones

# ==================== Tìm backbone trung tâm ====================
def find_central_backbone(backbones):
    def moment(bb):
        return sum(calculate_distance(bb, other) * other.weight for other in backbones if other.id != bb.id)
    return min(backbones, key=moment)

# ==================== Thuật toán MENTOR đầy đủ ====================
def mentor_algorithm():
    nodes = initialize_network()
    backbones = find_initial_backbones(nodes)
    print("Backbone ban đầu:", [n.id for n in backbones])

    max_cost = calculate_max_distance(nodes)
    threshold_distance = RADIUS_RATIO * max_cost
    print(f"Bán kính truy nhập = R * MaxCost = {threshold_distance:.2f}")

    assigned_ids = set(bb.id for bb in backbones)
    access_map = assign_access_nodes(nodes, backbones, threshold_distance, assigned_ids)

    while len(assigned_ids) < len(nodes):
        unassigned = [n for n in nodes if n.id not in assigned_ids]
        total_weight = sum(n.weight for n in unassigned)
        center_x = sum(n.x * n.weight for n in unassigned) / total_weight
        center_y = sum(n.y * n.weight for n in unassigned) / total_weight

        max_dist = max(calculate_distance(Node(-1, center_x, center_y, 0), n) for n in unassigned)
        max_weight = max(n.weight for n in unassigned)

        best_node = max(unassigned, key=lambda n: calculate_award(n, center_x, center_y, max_dist, max_weight))
        best_node.is_backbone = True
        backbones.append(best_node)
        print(f"→ Chọn node {best_node.id} làm backbone theo thưởng")

        new_map = assign_access_nodes(nodes, [best_node], threshold_distance, assigned_ids)
        access_map[best_node.id] = new_map.get(best_node.id, [])

    central_bb = find_central_backbone(backbones)
    print(f"Backbone trung tâm: {central_bb.id}")

    # ===== Ghi ra file =====
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("Backbone cuối cùng: " + str([n.id for n in backbones]) + "\n")
        f.write(f"Backbone trung tâm: {central_bb.id}\n\n")
        for bb in backbones:
            f.write(f"Backbone {bb.id}: {access_map.get(bb.id, [])}\n")
    print(f"\nKết quả đã được ghi vào '{OUTPUT_FILE}'.")
    return nodes, backbones, access_map

# ==================== Vẽ topology ====================
def draw_topology(nodes, backbones, access_map):
    for node in nodes:
        color = "red" if node.is_backbone else "blue"
        plt.scatter(node.x, node.y, c=color)
        plt.text(node.x, node.y, str(node.id), fontsize=8)
    for bb in backbones:
        for acc_id in access_map.get(bb.id, []):
            acc = next(n for n in nodes if n.id == acc_id)
            plt.plot([bb.x, acc.x], [bb.y, acc.y], 'gray', linestyle="--", linewidth=0.5)
    plt.title("Backbone and Access Nodes")
    plt.show()

# ==================== Thực thi ====================
if __name__ == "__main__":
    nodes, backbones, access_map = mentor_algorithm()
    draw_topology(nodes, backbones, access_map)
