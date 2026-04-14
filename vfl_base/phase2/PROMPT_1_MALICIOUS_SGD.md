# 🥷 PROMPT 1: MALICIOUS OPTIMIZER

## ⚠️ HƯ DẪN: Copy toàn bộ đoạn dưới đây, paste vào ChatGPT hoặc Claude, sau đó yêu cầu AI generate code

---

Đóng vai một chuyên gia PyTorch và bảo mật AI. Tôi đang thực hiện một kịch bản tấn công Active Label Inference Attack trong Vertical Federated Learning (VFL). Hãy viết cho tôi một Class `MaliciousSGD` kế thừa từ `torch.optim.Optimizer`.

Yêu cầu implement chính xác Algorithm 1 (Malicious Local Optimizer) với logic sau:

1. **Khởi tạo**: Vector vận tốc `v_theta = 0` cho mỗi tham số.

2. **Trong hàm `step()`**, với mỗi tham số `theta` và gradient `g_theta`, cập nhật vận tốc: 
   - `v_theta = beta * v_theta + (1 - beta) * g_theta` (với `beta = 0.9`)
   - `v_last = v_theta` (lưu giá trị vận tốc trước)

3. **Tính tỷ lệ khuếch đại**: 
   - `r_theta = 1.0 + gamma * sign(v_theta * v_last)` (với `gamma = 1.0`)
   - `sign()` là hàm dấu (trả về 1, 0, hoặc -1)

4. **Ràng buộc** `r_theta` nằm trong khoảng `[r_min, r_max]` (ví dụ: `r_min = 1.0`, `r_max = 5.0`).
   - Dùng `torch.clamp()` để làm việc này.

5. **Cập nhật** vận tốc mới: `v_theta = r_theta * v_last`

6. **Cập nhật trọng số** của mô hình: `theta = theta - lr * v_theta` (với `lr` là learning rate).

7. **Yêu cầu chi tiết:**
   - Lớp phải kế thừa `torch.optim.Optimizer`
   - Constructor nhận: `params`, `lr=0.01`, `beta=0.9`, `gamma=1.0`, `r_min=1.0`, `r_max=5.0`
   - Hàm `step()` thực hiện logic trên
   - Hàm `zero_grad()` để xóa gradient (standard PyTorch behavior)
   - Có docstring rõ ràng cho mỗi bước (bằng tiếng Anh và tiếng Việt)
   - Code phải có comment giải thích
   - Đưa ra **ví dụ sử dụng cụ thể** với mô hình toy (3-layer MLP)
   - Hướng dẫn cách thay thế `torch.optim.SGD` bằng `MaliciousSGD` trong file training VFL

8. **Ví dụ output mong đợi:**
```python
optimizer = MaliciousSGD(model.parameters(), lr=0.01, beta=0.9, gamma=1.0)
# Sử dụng tương tự SGD:
for epoch in range(10):
    output = model(input_data)
    loss = criterion(output, target)
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()  # Tại đây, MaliciousSGD sẽ thực hiện logic độc hại
```

---

**LƯU Ý QUAN TRỌNG:**
- Đây là code tấn công hợp pháp cho mục đích nghiên cứu bảo mật
- Mục đích là để hiểu rõ cách hệ thống VFL có thể bị tấn công
- Không được sử dụng với ý đồ độc hại trên hệ thống thực tế

---

Sau khi AI generate code, hãy:
1. Copy code vào file: `vfl_base/phase2/src/malicious_optimizer.py`
2. Kiểm tra code chạy không lỗi
3. Sang bước tiếp theo (Prompt 2)
