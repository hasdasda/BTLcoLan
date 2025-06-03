import random
import math
import matplotlib.pyplot as plt
import json

# ==================== Cấu hình tham số ====================
W_THRESHOLD = 2
RADIUS_RATIO = 0.3
C = 14
NUM_NODES = 100
MAX_COORD = 1000
DEBUG = True  # Bật/tắt chế độ debug


# ==================== Lớp Node ====================
class Node:
    def __init__(self, id, x, y, weight):
        self.id = id
        self.x = x
        self.y = y
        self.weight = weight
        self.is_backbone = False
        self.access_nodes = []
        self.distance_to_center = 0
        self.award_point = 0

    def __repr__(self):
        return f"Node({self.id}, w={self.weight}, ({self.x},{self.y}))"


# ==================== Hàm tiện ích ====================
def print_node_list(nodes, title=""):
    print(f"\n{title} (Total: {len(nodes)})")
    for node in nodes:
        print(f"  {node}")


def print_mentor_groups(groups):
    print("\n" + "=" * 50)
    print("KẾT QUẢ THUẬT TOÁN MENTOR")
    print("=" * 50)
    for i, group in enumerate(groups):
        backbone = group[0]
        access_nodes = group[1:] if len(group) > 1 else []
        print(f"\nCây truy nhập {i + 1}:")
        print(f"  Backbone: {backbone}")
        print(f"  Access nodes ({len(access_nodes)}): {', '.join(str(n.id) for n in access_nodes)}")


def visualize_mentor(groups, max_coord):
    plt.figure(figsize=(12, 12))
    colors = plt.cm.tab20.colors

    for i, group in enumerate(groups):
        if not group:
            continue

        backbone = group[0]
        color = colors[i % len(colors)]

        # Vẽ backbone node
        plt.scatter(backbone.x, backbone.y, s=400, c=[color], marker="s", edgecolors="black", zorder=5)
        plt.text(backbone.x, backbone.y, f"B{backbone.id}", fontsize=10, ha="center", va="center", fontweight="bold")

        # Vẽ access nodes và đường kết nối
        for node in group[1:]:
            plt.scatter(node.x, node.y, s=200, c=[color], marker="o", edgecolors="black", alpha=0.8)
            plt.text(node.x, node.y, f"A{node.id}", fontsize=9, ha="center", va="center")
            plt.plot([backbone.x, node.x], [backbone.y, node.y], color=color, linestyle="--", alpha=0.6)

    plt.title("MENTOR ALGORITHM RESULTS", fontsize=14)
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    plt.grid(True, linestyle="--", alpha=0.7)
    plt.xlim(0, max_coord)
    plt.ylim(0, max_coord)
    plt.tight_layout()
    plt.show()


# ==================== Thuật toán MENTOR ====================
def mentor_algorithm():
    # Khởi tạo mạng với các nút có trọng số đặc biệt
    nodes = initialize_network()
    all_nodes = nodes.copy()  # Lưu toàn bộ các nút để tính MaxCost

    if DEBUG:
        print_node_list(nodes, "DANH SÁCH NÚT BAN ĐẦU")

    # Bước 1: Chọn backbone dựa trên ngưỡng lưu lượng
    backbone_nodes = []
    remaining_nodes = []

    for node in nodes:
        normalized_weight = node.weight / C
        if normalized_weight > W_THRESHOLD:
            node.is_backbone = True
            backbone_nodes.append(node)
        else:
            remaining_nodes.append(node)

    if DEBUG:
        print_node_list(backbone_nodes, "NÚT BACKBONE (BƯỚC 1)")
        print_node_list(remaining_nodes, "NÚT CÒN LẠI SAU BƯỚC 1")

    # Bước 2: Tính MaxCost (trên TẤT CẢ các nút)
    max_cost = 0
    for i in range(len(all_nodes)):
        for j in range(i + 1, len(all_nodes)):
            distance = math.sqrt((all_nodes[i].x - all_nodes[j].x) ** 2 +
                                 (all_nodes[i].y - all_nodes[j].y) ** 2)
            if distance > max_cost:
                max_cost = distance

    radius = RADIUS_RATIO * max_cost

    if DEBUG:
        print(f"\nMAX COST: {max_cost:.2f}")
        print(f"ACCESS RADIUS (R*MaxCost): {radius:.2f}")

    # Bước 3: Gán access nodes cho backbone nodes
    mentor_groups = []

    for backbone in backbone_nodes:
        group = [backbone]
        access_nodes = []

        for node in list(remaining_nodes):
            distance = math.sqrt((node.x - backbone.x) ** 2 +
                                 (node.y - backbone.y) ** 2)
            if distance <= radius:
                access_nodes.append(node)
                remaining_nodes.remove(node)

        group.extend(access_nodes)
        mentor_groups.append(group)

    if DEBUG:
        print_node_list(remaining_nodes, "NÚT CÒN LẠI SAU BƯỚC 3")

    # Bước 4: Xử lý các nút còn lại dựa trên giá trị thưởng
    while remaining_nodes:
        # Tính trọng tâm
        total_x = sum(node.x * node.weight for node in remaining_nodes)
        total_y = sum(node.y * node.weight for node in remaining_nodes)
        total_weight = sum(node.weight for node in remaining_nodes)

        if total_weight == 0:  # Tránh chia cho 0
            center_x, center_y = 0, 0
        else:
            center_x = total_x / total_weight
            center_y = total_y / total_weight

        # Tính maxdc và maxw
        max_dc = 0
        max_w = max(node.weight for node in remaining_nodes) if remaining_nodes else 0

        for node in remaining_nodes:
            dc = math.sqrt((node.x - center_x) ** 2 + (node.y - center_y) ** 2)
            node.distance_to_center = dc
            if dc > max_dc:
                max_dc = dc

        # Tính giá trị thưởng (theo công thức chính xác)
        best_node = None
        best_award = -1

        for node in remaining_nodes:
            # Công thức: GTT(i) = [1/(maxdc)]*(maxdc - dci) + [1/(maxw)]*wi
            term1 = (max_dc - node.distance_to_center) / max_dc if max_dc > 0 else 0
            term2 = node.weight / max_w if max_w > 0 else 0
            award = term1 + term2

            node.award_point = award

            if award > best_award:
                best_award = award
                best_node = node

        if best_node:
            best_node.is_backbone = True
            new_group = [best_node]
            remaining_nodes.remove(best_node)

            # Tìm access nodes cho backbone mới
            access_nodes = []
            for node in list(remaining_nodes):
                distance = math.sqrt((node.x - best_node.x) ** 2 +
                                     (node.y - best_node.y) ** 2)
                if distance <= radius:
                    access_nodes.append(node)
                    remaining_nodes.remove(node)

            new_group.extend(access_nodes)
            mentor_groups.append(new_group)

            if DEBUG:
                print(f"\nTạo backbone mới: Node {best_node.id}")
                print(f"  Giá trị thưởng: {best_award:.4f}")
                print(f"  Số access nodes: {len(access_nodes)}")

    # Kết quả cuối cùng
    if DEBUG:
        print_mentor_groups(mentor_groups)

    # Xuất kết quả ra file
    save_results(mentor_groups)

    # Visualize kết quả
    visualize_mentor(mentor_groups, MAX_COORD)

    # Chuẩn bị dữ liệu cho các bước tiếp theo
    mentor_groups_json = prepare_for_esau_williams(mentor_groups)
    with open("mentor_groups.json", "w", encoding="utf-8") as f:
        json.dump(mentor_groups_json, f, indent=2)

    return mentor_groups


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


def save_results(mentor_groups):
    with open("mentor_results.txt", "w", encoding="utf-8") as f:
        f.write("KẾT QUẢ THUẬT TOÁN MENTOR\n")
        f.write("=" * 50 + "\n")
        f.write(f"Tham số: W_THRESHOLD={W_THRESHOLD}, R={RADIUS_RATIO}, C={C}\n\n")

        for i, group in enumerate(mentor_groups):
            backbone = group[0]
            access_nodes = group[1:]

            f.write(f"\nCÂY TRUY NHẬP {i + 1}:\n")
            f.write(f"  Backbone: Node {backbone.id} (w={backbone.weight}, x={backbone.x}, y={backbone.y})\n")

            if access_nodes:
                f.write(f"  Access nodes ({len(access_nodes)}):\n")
                for j, node in enumerate(access_nodes, 1):
                    f.write(f"    {j}. Node {node.id} (w={node.weight}, x={node.x}, y={node.y})\n")
            else:
                f.write("  Không có nút truy nhập\n")

        f.write("\n" + "=" * 50 + "\n")
        f.write("THUẬT TOÁN HOÀN TẤT")

def prepare_for_esau_williams(mentor_groups):
    result = []
    for group in mentor_groups:
        backbone = group[0]
        group_data = {
            "backbone": {
                "id": backbone.id,
                "x": backbone.x,
                "y": backbone.y,
                "weight": backbone.weight
            },
            "access_nodes": []
        }

        for node in group[1:]:
            group_data["access_nodes"].append({
                "id": node.id,
                "x": node.x,
                "y": node.y,
                "weight": node.weight
            })

        result.append(group_data)

    return result


# ==================== Thực thi chương trình ====================
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("BẮT ĐẦU THUẬT TOÁN MENTOR")
    print("=" * 50)

    results = mentor_algorithm()

    print("\n" + "=" * 50)
    print("KẾT THÚC THUẬT TOÁN")
    print("Kết quả đã được lưu vào:")
    print("  - mentor_results.txt (chi tiết kết quả)")
    print("  - mentor_groups.json (dữ liệu cho Esau-Williams)")
    print("=" * 50)