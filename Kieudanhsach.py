import random
import math
import csv

# Số nút
n_nodes = 100

# Tạo vị trí ngẫu nhiên cho mỗi nút trên mặt phẳng 1000x1000
positions = [(random.randint(0, 1000), random.randint(0, 1000)) for _ in range(n_nodes)]


# Tính khoảng cách giữa mọi cặp nút và lưu theo danh sách cạnh
edges = []
for i in range(n_nodes):
    for j in range(i + 1, n_nodes):
        x1, y1 = positions[i]
        x2, y2 = positions[j]
        distance = abs(x2 - x1) + abs(y2 - y1)
        edges.append((i, j, distance))

# Xuất ra file CSV
with open("edge_list.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Node1", "Node2", "Weight"])
    writer.writerows(edges)

print("Đã lưu danh sách cạnh vào file 'edge_list.csv'.")
