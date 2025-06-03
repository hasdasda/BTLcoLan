import random
import math

class Node:
  def __init__(self, ten, x, y):
    self.ten = ten
    self.x = x
    self.y = y

  def hien_thi(self):
    print(f"Điểm {self.ten}: ({self.x}, {self.y})")

def distance_formula(x1, y1, x2, y2):
  return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

# Tạo danh sách chứa 5 điểm (để dễ theo dõi, bạn có thể thay đổi thành 100)
danh_sach_diem = []
for i in range(1, 100):  # Thay đổi thành range(1, 100) để tạo 100 điểm
  ten_diem = f"P{i}"
  toa_do_x = random.randint(0, 1000)  # Phạm vi nhỏ hơn để dễ theo dõi
  toa_do_y = random.randint(0, 1000)
  diem = Node(ten_diem, toa_do_x, toa_do_y)
  danh_sach_diem.append(diem)

# Tạo danh sách cạnh đầy đủ
danh_sach_canh_day_du = []
for i in range(len(danh_sach_diem)):
  for j in range(i + 1, len(danh_sach_diem)):
    diem1 = danh_sach_diem[i]
    diem2 = danh_sach_diem[j]
    khoang_cach = distance_formula(diem1.x, diem1.y, diem2.x, diem2.y)
    danh_sach_canh_day_du.append(((diem1.ten, diem2.ten), khoang_cach))

# Hiển thị danh sách cạnh đầy đủ
print("\nDanh sách cạnh đầy đủ:")
for canh, khoang_cach in danh_sach_canh_day_du:
  print(f"Cạnh giữa {canh[0]} và {canh[1]}: Khoảng cách = {khoang_cach:.2f}")