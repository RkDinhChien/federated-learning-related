# 🥷 GIAI ĐOẠN 2: KẺ TẤN CÔNG XUẤT HIỆN

## 📌 Tổng Quan

Sau khi VFL Base System chạy thành công (Loss ↓38%, Accuracy ↑31%), bây giờ **Bảo** sẽ đóng vai **Client độc hại** để tấn công Server (Chiến) bằng cách ăn cắp nhãn dữ liệu.

**Mục tiêu tuần này:**
- Bảo viết code **Malicious Optimizer** + **MixMatch Inference Attack**
- Đạt **Attack Success Rate (ASR) > 75%**
- Chứng minh khả năng ăn cắp 80% dữ liệu nhạy cảm từ chỉ 40 nhãn mồi

---

## 🎯 Mục Tiêu Chi Tiết

### Phase 2.1: Tấn Công Chủ Động (Active Attack)
- ✅ Sửa Optimizer Client từ `SGD` → `MaliciousSGD`
- ✅ Thao túng gradient để ép Server phụ thuộc vào dữ liệu Client
- ✅ Server không biết mình bị tấn công

### Phase 2.2: Tấn Công Thụ Động (Passive Attack)
- ✅ Đóng băng BottomModel đã train
- ✅ Tạo InferenceHead kết nối vào BottomModel
- ✅ Dùng 40 nhãn mồi + MixMatch để đoán nhãn toàn dataset
- ✅ Tính **ASR (Attack Success Rate)**

---

## 📂 Cấu Trúc Files Phase 2

```
vfl_base/phase2/
├── src/
│   ├── malicious_optimizer.py      # MaliciousSGD class
│   ├── client_bao_attack.py         # Client tấn công (cập nhật từ phase1)
│   ├── inference_head.py            # InferenceHead + MixMatch
│   ├── main_attack.py               # Training loop với tấn công
│   └── utils.py                     # Hàm hỗ trợ (Sharpen, MixUp)
├── docs/
│   ├── ATTACK_EXPLANATION.md        # Giải thích thuật toán
│   └── RESULTS.md                   # Báo cáo kết quả
└── requirements_phase2.txt          # Dependencies thêm
```

---

## 🥷 PROMPT 1: MALICIOUS OPTIMIZER (Cho Bảo)

### ⚠️ COPY ĐOẠN NÀY ĐƯA CHO AI (ChatGPT/Claude)

```
Đóng vai một chuyên gia PyTorch và bảo mật AI. Tôi đang thực hiện một kịch bản tấn công Active Label Inference Attack trong Vertical Federated Learning (VFL). Hãy viết cho tôi một Class `MaliciousSGD` kế thừa từ `torch.optim.Optimizer`.

Yêu cầu implement chính xác Algorithm 1 (Malicious Local Optimizer) với logic sau:

1. Khởi tạo vector vận tốc $v_\theta = 0$ cho mỗi tham số.
2. Trong hàm `step()`, với mỗi tham số $\theta$ và gradient $g_\theta$, cập nhật vận tốc: 
   $v_\theta = \beta \cdot v_\theta + (1-\beta) \cdot g_\theta$ (với $\beta = 0.9$).
3. Tính tỷ lệ khuếch đại: 
   $r_\theta = 1.0 + \gamma \cdot \text{sign}(v_\theta \odot v_{last})$ (với $\gamma = 1.0$).
4. Ràng buộc $r_\theta$ nằm trong khoảng $[r_{min}, r_{max}]$ (ví dụ: $r_{min} = 1.0$, $r_{max} = 5.0$).
5. Cập nhật $v_\theta$ mới: $v_\theta = r_\theta \cdot v_{last}$
6. Cập nhật trọng số của mô hình: $\theta = \theta - \eta \cdot v_\theta$ (với $\eta$ là learning rate).
7. Hãy viết code thật rõ ràng, có comment giải thích tiếng Anh và tiếng Việt.
8. Cung cấp hướng dẫn cách thay thế `torch.optim.SGD` bằng `MaliciousSGD` trong file training.

Yêu cầu chi tiết:
- Lớp phải kế thừa `torch.optim.Optimizer`
- Constructor nhận: `params`, `lr=0.01`, `beta=0.9`, `gamma=1.0`, `r_min=1.0`, `r_max=5.0`
- Hàm `step()` thực hiện logic trên
- Có docstring rõ ràng cho mỗi bước
- Đưa ra ví dụ sử dụng
```

---

## 🥷 PROMPT 2: INFERENCE HEAD & MIXMATCH (Cho Bảo)

### ⚠️ COPY ĐOẠN NÀY ĐƯA CHO AI (ChatGPT/Claude)

```
Đóng vai chuyên gia PyTorch. Tôi đã train xong BottomModel (ResNet-18) trong hệ thống VFL. Bây giờ tôi muốn thực hiện Passive Label Inference Attack bằng thuật toán MixMatch.

Hãy viết cho tôi một module Python với các chức năng sau:

1. Class `InferenceHead`:
   - Đóng băng trọng số của `BottomModel` hiện tại.
   - Tạo một mạng Neural nhỏ gắn nối tiếp vào sau `BottomModel` (Fully Connected layers).
   - Lớp FC: embedding_dim (128) -> hidden_dim (256) -> num_classes (10)
   - Activation: ReLU, Dropout 0.3 giữa các lớp.
   - Đầu ra: logits cho 10 classes.

2. Hàm `sharpen(predictions, temperature=0.5)`:
   - Làm sắc nét phân phối xác suất.
   - Công thức: $\bar{p}(y|x) = \frac{p(y|x)^{1/T}}{\sum_y p(y|x)^{1/T}}$
   - Trả về pseudo-labels sắc nét.

3. Hàm `mixup(x1, x2, y1, y2, alpha=0.2)`:
   - Trộn dữ liệu có nhãn và không nhãn.
   - $\lambda \sim \text{Beta}(\alpha, \alpha)$
   - $\tilde{x} = \lambda x_1 + (1-\lambda) x_2$
   - $\tilde{y} = \lambda y_1 + (1-\lambda) y_2$
   - Trả về mixed samples và mixed labels.

4. Hàm `generate_auxiliary_labels(dataset, num_labels=40)`:
   - Chọn ngẫu nhiên 40 sample từ tập dữ liệu.
   - Tập X: 40 sample có nhãn thật.
   - Tập U: còn lại không có nhãn.
   - Trả về (X, U) tuple.

5. Hàm `train_inference_head(model, bottom_model, inference_head, X, U, epochs=50, lr=0.01)`:
   - Vòng lặp training độc lập cho InferenceHead.
   - Input X (có nhãn) và U (không nhãn).
   - Tính Loss tổng hợp: $L = L_X + \lambda_U \cdot L_U$
     - $L_X$: CrossEntropyLoss cho dữ liệu có nhãn
     - $L_U$: MSELoss cho pseudo-labels của dữ liệu không nhãn
     - $\lambda_U = 1.0$
   - Sau mỗi epoch, in ra training loss.
   - Trả về trained InferenceHead.

6. Hàm `calculate_asr(model, bottom_model, inference_head, U_data, U_labels)`:
   - Tính Attack Success Rate.
   - Đưa U_data qua BottomModel + InferenceHead.
   - Lấy predictions argmax để so sánh với U_labels thật.
   - $\text{ASR} = \frac{\text{số dự đoán đúng}}{\text{tổng U}} \times 100\%$
   - In ra: "Attack Success Rate: XX.XX%"
   - Trả về ASR (float).

Yêu cầu chi tiết:
- Tất cả code phải có comment rõ ràng (tiếng Anh + tiếng Việt).
- Sử dụng PyTorch (torch, torch.nn, torch.optim).
- Có docstring cho mỗi hàm.
- Cung cấp ví dụ sử dụng toàn bộ module.
- Hướng dẫn tích hợp vào file `main_attack.py` để sau training chung, tự động chạy attack.
```

---

## 📋 Các Bước Thực Hiện Cho Bảo

### Bước 1: Tạo File `malicious_optimizer.py`
```bash
# Bảo copy Prompt 1 vào ChatGPT/Claude
# Lấy code ra, lưu vào: vfl_base/phase2/src/malicious_optimizer.py
```

### Bước 2: Tạo File `inference_head.py`
```bash
# Bảo copy Prompt 2 vào ChatGPT/Claude
# Lấy code ra, lưu vào: vfl_base/phase2/src/inference_head.py
```

### Bước 3: Cập Nhật `client_bao.py`
```python
# Thay dòng này:
from torch.optim import SGD

# Thành dòng này:
from malicious_optimizer import MaliciousSGD
self.optimizer = MaliciousSGD(self.model.parameters(), lr=learning_rate)
```

### Bước 4: Tạo `main_attack.py`
```python
# Copy main.py từ phase1/src/main.py
# Thêm code sau training loop:

from inference_head import (
    generate_auxiliary_labels,
    train_inference_head,
    calculate_asr,
    InferenceHead
)

# Sau khi train xong:
X, U = generate_auxiliary_labels(test_dataset, num_labels=40)
inference_head = InferenceHead(embedding_dim=128)
inference_head = train_inference_head(
    client.model, 
    inference_head, 
    X, U, 
    epochs=50
)
asr = calculate_asr(client.model, inference_head, U)

print(f"🥷 Attack Success Rate: {asr:.2f}%")
```

### Bước 5: Chạy và Báo Cáo
```bash
cd vfl_base/phase2/src
python main_attack.py

# Output mong đợi:
# 🥷 Attack Success Rate: 78.50%
```

---

## 🎯 Tiêu Chí Thành Công

| Tiêu Chí | Mục Tiêu | Trạng Thái |
|---------|---------|-----------|
| MaliciousSGD hoạt động | ✅ Code chạy không lỗi | Pending |
| InferenceHead training | ✅ Loss giảm qua epochs | Pending |
| ASR >= 75% | ✅ Ăn cắp >= 75% nhãn | Pending |
| Chiến không biết bị tấn công | ✅ Server vẫn train bình thường | ✅ Yes |

---

## 📊 Kỳ Vọng Kết Quả

```
Epoch 1/50 - Loss_X: 0.8234, Loss_U: 0.6123, Total: 1.4357
Epoch 2/50 - Loss_X: 0.7123, Loss_U: 0.5234, Total: 1.2357
...
Epoch 50/50 - Loss_X: 0.1234, Loss_U: 0.0923, Total: 0.2157

🥷 Attack Success Rate: 78.50%
🎉 BẢO ĐÃ THÀNH CÔNG ĂNCẮP DỮ LIỆU!
```

---

## 💡 Ghi Chú Quan Trọng

1. **Bảo không cần sửa Server code** - chỉ sửa Client thôi
2. **MaliciousSGD là "lén lút"** - Chiến không biết bị tấn công
3. **40 nhãn mồi** - simulate Bảo đã mua/mua chuộc được
4. **MixMatch** - kết hợp labeled + unlabeled data
5. **ASR > 75%** - chứng minh tấn công thành công

---

## 🚀 Khi Nào Báo Lại?

Khi Bảo chạy xong và in ra:
```
🥷 Attack Success Rate: XX.XX%
```

Nếu **ASR > 75%** → **Quay lại đây, tui tung PROMPT GIAI ĐOẠN 3** (Thuật toán phòng thủ FLSG cho Chiến) 🛡️

---

## 📚 Tài Liệu Tham Khảo

- **MixMatch Paper**: [arXiv:1905.02249](https://arxiv.org/abs/1905.02249)
- **Label Inference Attack**: USENIX 2022 (Passive Label Inference Attacks in Vertical Federated Learning)
- **Momentum Optimizer**: PyTorch SGD with momentum

---

**Chúc Bảo viết mã độc thành công!** 🥷💻
