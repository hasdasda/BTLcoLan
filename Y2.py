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
DEBUG = False  # Thêm biến DEBUG để điều khiển in ấn gỡ lỗi
LIMIT_ACCESS_NODES = 0 # Thêm giới hạn cho số lượng access nodes

# ==================== Lớp Node ====================
class Node:
    def __init__(self, id, x, y, weight, traffic=0, distance=0, award=0):
        self.id = id
        self.x = x
        self.y = y
        self.weight = weight
        self.is_backbone = False
        self.access_nodes = []
        self.traffic = traffic
        self.distance_to_center = distance
        self.award_point = award

    def get_id(self): return self.id
    def get_position_x(self): return self.x
    def get_position_y(self): return self.y
    def get_weight(self): return self.weight
    def get_traffic(self): return self.traffic
    def set_distance(self, center_node):
        self.distance_to_center = math.sqrt((self.x - center_node.x)**2 + (self.y - center_node.y)**2)
    def get_distance(self): return self.distance_to_center
    def set_award(self, award): self.award_point = award
    def get_award(self): return self.award_point

    def print_node(self):
        print(f"Node {self.id}: x={self.x}, y={self.y}, weight={self.weight}, traffic={self.traffic}")

def printMentorList(node_list):
    for node in node_list:
        node.print_node()

def printList2D(list_of_lists):
    for inner_list in list_of_lists:
        for node in inner_list:
            print(node.get_id(), end=' ')
        print()

def matplot_mentor(mentor_list, max_coord):
    plt.figure(figsize=(10, 10))
    for group in mentor_list:
        if group:
            backbone = group[0]
            plt.scatter(backbone.x, backbone.y, color='red', s=100, label='Backbone' if group == mentor_list[0] else "")
            plt.text(backbone.x, backbone.y, str(backbone.id), fontsize=9)
            for i in range(1, len(group)):
                terminal_node = group[i]
                plt.scatter(terminal_node.x, terminal_node.y, color='blue', s=50, label='Access Node' if group == mentor_list[0] and i == 1 else "")
                plt.plot([backbone.x, terminal_node.x], [backbone.y, terminal_node.y], 'gray', linestyle='--')
                plt.text(terminal_node.x, terminal_node.y, str(terminal_node.id), fontsize=8)
    plt.xlim(0, max_coord)
    plt.ylim(0, max_coord)
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    plt.title("MENTOR Algorithm Result")
    plt.legend()
    plt.grid(True)
    plt.show()

class CenterNode:
    def __init__(self):
        self.x = 0
        self.y = 0

    def set_position(self, x, y):
        self.x = x
        self.y = y

    def printCenterPress(self):
        print(f"Tọa độ trọng tâm: x={round(self.x, 2)}, y={round(self.y, 2)}")

def copyNode(source_node):
    new_node = Node(source_node.id, source_node.x, source_node.y, source_node.weight, source_node.traffic)
    return new_node

# ==================== Hàm tính toán (giữ nguyên) ====================
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

# ==================== Khởi tạo mạng (sửa để có traffic) ====================
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
        # Giả định traffic bằng weight cho đơn giản, bạn có thể điều chỉnh
        traffic = weight
        nodes.append(Node(i, x, y, weight, traffic))
    return nodes

# ==================== Thuật toán MENTOR (đã sửa đổi và tích hợp vẽ + xuất file) ====================
def mentor_algorithm():
    ListPosition = initialize_network()
    ListMentor = []
    w = W_THRESHOLD
    RadiusRatio = RADIUS_RATIO
    Limit = LIMIT_ACCESS_NODES
    DeBug = DEBUG
    MAX = MAX_COORD
    C_param = C

    '''

    Bước 2: Tìm Nút Backbone và phân cây truy nhập dựa trên thuật toán MENTOR

    '''
    print("{:*<100}".format(''))
    print("Bước 2: Tìm Nút Backbone và phân cây truy nhập dựa trên thuật toán MENTOR")
    print("{:*<100}".format(''))

    ListBackboneType1 = []

    for i in list(ListPosition): # Iterate over a copy to allow removal
        if i.get_traffic() / C_param > w:
            ListBackboneType1.append(i)
            ListPosition.remove(i)

    if DeBug:
        print("2.1. List Backbone do lưu lượng chuẩn hóa lớn hơn ngưỡng")
        printMentorList(ListBackboneType1)


    # Tìm MaxCost
    if DeBug:
        print("Tìm MaxCost và R*MaxCost")
    MaxCost = 0
    for i in range(len(ListPosition)):
        for j in range(i + 1, len(ListPosition)):
            dc = math.sqrt((ListPosition[i].get_position_x() - ListPosition[j].get_position_x()) ** 2 + (
                    ListPosition[i].get_position_y() - ListPosition[j].get_position_y()) ** 2)
            if dc > MaxCost:
                MaxCost = dc

    RM = RadiusRatio * MaxCost
    if DeBug:
        print('MaxCost = {:<8} & R*MaxCost = {:<8}'.format(round(MaxCost,3), round(RM,3)))

    # Dựng hàm cập nhật các nút đầu cuối cho các nút backbone

    DEBUG_UpdateTerminalNode = 0

    def updateTerminalNode(_ListPosition, _ListMentor, _centerNode):

        if DEBUG_UpdateTerminalNode:
            print("Enter Update Terminal Node Function! ")
            print("Node backbone", _centerNode.get_id())

        # Kiểm tra khoảng cách các node so với node backbone
        ListBackbone = []
        ListBackbone.append(_centerNode)

        def check_non_exist(index,listbackbone,listmentor):
            if DEBUG_UpdateTerminalNode:
                for i in listbackbone:
                    print(i.get_id(),end =' ')
                print()
                for i in listmentor:
                    for j in i:
                        print(j.get_id(), end=' ')
                print()
            for i in listbackbone:
                if i.get_id() == index:
                    if DEBUG_UpdateTerminalNode:
                        print("in list backbone. no check any more")
                    return False
            for i in listmentor:
                for j in i:
                    if j.get_id() == index:
                        if DEBUG_UpdateTerminalNode:
                            print("in list mentor. no check any more")
                        return False
            return True

        for i in list(_ListPosition): # Iterate over a copy
            i.set_distance(_centerNode)
            if DEBUG_UpdateTerminalNode:
                print("Check Distance Node", i.get_id(), " : ", i.get_distance())
            if check_non_exist(i.get_id(),ListBackbone,_ListMentor):
                if i.get_distance() <= RM:
                    if DEBUG_UpdateTerminalNode:
                        print("Node", i.get_id(), "is terminal node of Node center", _centerNode.get_id())
                    ListBackbone.append(i)

        # Xử lý giới hạn số nút đầu cuối của nút backbone

        def sort_by_distance_to_backbone(m):
            return  m.get_distance()

        ListBackbone.sort(key=sort_by_distance_to_backbone)

        if Limit > 0:
            if DEBUG_UpdateTerminalNode:
                for i in ListBackbone:
                    print(i.get_id(),end =' ')
                print()
            if len(ListBackbone)-1 > Limit:
                ListBackbone = ListBackbone[0:Limit+1]
            if DEBUG_UpdateTerminalNode:
                for i in ListBackbone:
                    print(i.get_id(),end =' ')
                print()

        _ListMentor.append(ListBackbone)

        for i in list(ListBackbone): # Iterate over a copy
            for j in list(_ListPosition): # Iterate over a copy
                if i.get_id() == j.get_id() and j in _ListPosition:
                    _ListPosition.remove(j)

        if DEBUG_UpdateTerminalNode:
            print("Exit Update Terminal Node Function! ")


    for i in ListBackboneType1:
        updateTerminalNode(ListPosition, ListMentor, i)

    del ListBackboneType1
    if DeBug:
        print("-----------Danh sách các nút Backbone và cây truy nhập đi kèm sau khi tìm Backbone dựa trên ngưỡng lưu lượng -----------")
        printList2D(ListMentor)
        print("-----------Dach sách các nút còn lại chưa được phân cây truy nhập-----------")
        printMentorList(ListPosition)


    '''

    Bước 3: Đối với các nút còn lại, tiến hành tìm nút backbone dựa trên giá trị thưởng, sau đó cập nhật các nút đầu cuối

    '''
    if DeBug:
        print()
        print(
        "2.2. Đối với các nút còn lại, tiến hành tìm nút Backbone dựa trên giá trị thưởng, sau đó cập nhật cây truy nhập tương ứng với nút Backbone mới")
        print()
    center = CenterNode()
    iloop = 1
    while len(ListPosition) > 0:
        if DeBug:
            print("Vòng lặp tìm giá trị thưởng lần", iloop)
        iloop = iloop + 1
        # Tìm trung tâm trọng lực
        sumx = 0
        sumy = 0
        sumw = 0
        xtt = 0
        ytt = 0
        maxw = 1
        maxdc = 1
        maxaward = 0
        indexBB = 0

        for i in ListPosition:
            sumx = sumx + (i.get_position_x()) * i.get_traffic()
            sumy = sumy + (i.get_position_y()) * i.get_traffic()
            sumw = sumw + i.get_traffic()
            if i.get_traffic() > maxw:
                maxw = i.get_traffic()
        xtt = sumx / sumw
        ytt = sumy / sumw

        center.set_position(xtt, ytt)

        if DeBug:
            center.printCenterPress()

        for i in ListPosition:
            i.set_distance(center)
            if i.get_distance() > maxdc:
                maxdc = i.get_distance()
        if DeBug:
            print("MaxDistance = {:<6} & Max Weight: {:<3}".format(round(maxdc,2), maxw))
        for i in ListPosition:
            i.set_award((0.5 * (maxdc - i.get_distance() / maxdc)) + (0.5 * i.get_traffic() / maxw))
            if i.get_award() > maxaward:
                maxaward = i.get_award()

        best_node_to_become_bb = None
        for i in ListPosition:
            if i.get_award() >= maxaward:
                best_node_to_become_bb = copyNode(i)
                if DeBug:
                    print("Nút Thưởng được chọn làm backbone: {:<3}".format(best_node_to_become_bb.get_id()))
                ListPosition.remove(i)
                if DeBug:
                    print("--- Danh sách các nút còn lại sau khi bỏ nút backbone ---")
                    printMentorList(ListPosition)
                if DeBug:
                    print("---------------------")
                    print("Cập nhật cây truy nhập cho nút backbone mới")
                updateTerminalNode(ListPosition, ListMentor, best_node_to_become_bb)
                if DeBug:
                    print("---------------------")
                    print("--- Danh sách các nút còn lại sau khi cập nhật cây truy nhập cho nút backbone mới ---")
                    printMentorList(ListPosition)
                    print("---------------------")
                break

    '''

    Kết thúc thuật toán, hiển thị kết quả và ghi ra file

    '''

    if DeBug:
        print("-------Kết quả thuật toán Mentor-------")
        printList2D(ListMentor)

    matplot_mentor(ListMentor,MAX)

    # Ghi kết quả ra file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("Kết quả thuật toán MENTOR:\n")
        for i, group in enumerate(ListMentor):
            if group:
                backbone = group[0]
                access_nodes = [node.get_id() for node in group[1:]]
                f.write(f"Cây truy nhập {i+1}:\n")
                f.write(f"  Backbone: Node {backbone.get_id()} (x={backbone.get_position_x()}, y={backbone.get_position_y()}, weight={backbone.get_weight()}, traffic={backbone.get_traffic()})\n")
                if access_nodes:
                    f.write(f"  Access Nodes: {access_nodes}\n")
                else:
                    f.write("  Không có nút truy nhập.\n")
            else:
                f.write(f"Cây truy nhập {i+1}: Rỗng\n")

    print(f"\nThông tin các nút backbone và nút truy nhập đã được ghi vào file: {OUTPUT_FILE}")
    # ===== Tạo dữ liệu đầu vào cho Esau-Williams =====
    mentor_groups = []
    for group in ListMentor:
        if group:
            backbone = group[0]
            access_nodes = group[1:]

            group_info = {
                "backbone": {
                    "id": backbone.get_id(),
                    "x": backbone.get_position_x(),
                    "y": backbone.get_position_y(),
                    "weight": backbone.get_weight(),
                    "traffic": backbone.get_traffic()
                },
                "access_nodes": []
            }

            for node in access_nodes:
                group_info["access_nodes"].append({
                    "id": node.get_id(),
                    "x": node.get_position_x(),
                    "y": node.get_position_y(),
                    "weight": node.get_weight(),
                    "traffic": node.get_traffic()
                })

            mentor_groups.append(group_info)

    return ListMentor, mentor_groups
# ==================== Thực thi ====================
if __name__ == "__main__":
    mentor_result, mentor_groups = mentor_algorithm()
    print("\nKết quả thuật toán Mentor (danh sách các cây truy nhập):")
    printList2D(mentor_result)

    # Ghi mentor_groups ra file JSON sau khi thuật toán Mentor hoàn thành
    import json
    with open("mentor_groups.json", "w", encoding="utf-8") as f:
        json.dump(mentor_groups, f, indent=2)
    print("\nDữ liệu mentor_groups đã được ghi vào file 'mentor_groups.json'")
