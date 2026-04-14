# 🥷 PROMPT 2: INFERENCE HEAD & MIXMATCH

## ⚠️ HƯỚNG DẪN: Copy toàn bộ đoạn dưới đây, paste vào ChatGPT hoặc Claude, sau đó yêu cầu AI generate code

---

Đóng vai chuyên gia PyTorch. Tôi đã train xong BottomModel (ResNet-18) trong hệ thống VFL. Bây giờ tôi muốn thực hiện Passive Label Inference Attack bằng thuật toán MixMatch.

Hãy viết cho tôi một module Python với các chức năng sau:

## 1. Class `InferenceHead`

```python
class InferenceHead(nn.Module):
    """
    Đóng băng trọng số của BottomModel hiện tại.
    Tạo một mạng Neural nhỏ gắn nối tiếp vào sau BottomModel.
    Cấu trúc:
    - Input: embedding_dim (128-dim từ BottomModel)
    - Hidden layer 1: 128 -> 256, ReLU, Dropout(0.3)
    - Hidden layer 2: 256 -> 128, ReLU, Dropout(0.3)
    - Output layer: 128 -> 10 (num_classes)
    """
```

Yêu cầu:
- Kế thừa từ `nn.Module`
- Constructor nhận: `embedding_dim`, `hidden_dim=256`, `num_classes=10`, `dropout_rate=0.3`
- Hàm `forward()` nhận embedding từ BottomModel, trả về logits
- Code phải có docstring và comment rõ ràng

---

## 2. Hàm `sharpen(predictions, temperature=0.5)`

Làm sắc nét phân phối xác suất.
- Công thức: `p_sharp = p^(1/T) / sum(p^(1/T))`
- Input: `predictions` - tensor chứa probabilities (shape: [batch_size, num_classes])
- Input: `temperature` - giá trị T (mặc định 0.5)
- Output: `pseudo_labels` - tensor gồm xác suất sắc nét

Ví dụ:
```python
# Trước sharpen: [0.3, 0.3, 0.2, 0.2]
# Sau sharpen:  [0.5, 0.5, 0.0, 0.0]  # Sắc nét hơn
```

---

## 3. Hàm `mixup(x1, x2, y1, y2, alpha=0.2)`

Trộn dữ liệu có nhãn và không nhãn.
- Lấy `lambda ~ Beta(alpha, alpha)`
- Tính `x_mixed = lambda * x1 + (1 - lambda) * x2`
- Tính `y_mixed = lambda * y1 + (1 - lambda) * y2`
- Input: `x1, x2` - input data, `y1, y2` - labels (hoặc pseudo-labels), `alpha` - Beta parameter
- Output: `(x_mixed, y_mixed)` tuple

---

## 4. Hàm `generate_auxiliary_labels(dataset, num_labels=40)`

Chọn ngẫu nhiên 40 sample từ tập dữ liệu (mô phỏng Bảo đã mua chuộc được 40 nhãn).
- Tập X: 40 sample có nhãn thật (labeled set)
- Tập U: còn lại ~ 9960 sample không có nhãn (unlabeled set)
- Input: `dataset` - CIFAR-10 dataset, `num_labels=40` - số nhãn mồi
- Output: `(X, U)` tuple, trong đó:
  - `X = (images_X, labels_X)` - 40 labeled samples
  - `U = (images_U, labels_U_true)` - ~9960 unlabeled samples (labels_U_true giữ kín để tính ASR sau)

---

## 5. Hàm `train_inference_head(bottom_model, inference_head, X, U, epochs=50, lr=0.01, device='cpu')`

Vòng lặp training độc lập cho InferenceHead.
- Đóng băng `bottom_model` (không cập nhật weights)
- Input:
  - `bottom_model` - BottomModel đã train (ResNet-18)
  - `inference_head` - InferenceHead chưa train
  - `X = (images_X, labels_X)` - labeled data (40 samples)
  - `U = (images_U, labels_U_true)` - unlabeled data (~9960 samples)
  - `epochs` - số vòng lặp (mặc định 50)
  - `lr` - learning rate (mặc định 0.01)
  - `device` - 'cuda' hoặc 'cpu'
- Logic:
  1. Nạp batch từ X và U
  2. Đưa X qua BottomModel (frozen) + InferenceHead → logits_X
  3. Tính Loss_X = CrossEntropyLoss(logits_X, labels_X)
  4. Đưa U qua BottomModel (frozen) + InferenceHead → logits_U
  5. Tính pseudo-labels bằng sharpen(softmax(logits_U))
  6. Tính Loss_U = MSELoss(softmax(logits_U), pseudo_labels)
  7. Loss tổng = Loss_X + lambda_U * Loss_U (với lambda_U = 1.0)
  8. Backward và update InferenceHead
  9. Sau mỗi epoch, in ra: `"Epoch {ep}/{epochs} - Loss_X: {loss_x:.4f}, Loss_U: {loss_u:.4f}, Total: {total_loss:.4f}"`
- Output: `inference_head` đã train
- Có docstring rõ ràng và comment chi tiết

---

## 6. Hàm `calculate_asr(bottom_model, inference_head, U_images, U_labels_true, device='cpu')`

Tính Attack Success Rate.
- Input:
  - `bottom_model` - BottomModel đã train (frozen)
  - `inference_head` - InferenceHead đã train (từ hàm 5)
  - `U_images` - ảnh từ tập U (~9960 samples)
  - `U_labels_true` - nhãn thật của U (dùng để so sánh)
  - `device` - 'cuda' hoặc 'cpu'
- Logic:
  1. Đưa U_images qua BottomModel (frozen) + InferenceHead → logits
  2. Lấy predictions = argmax(logits)
  3. So sánh predictions với U_labels_true
  4. ASR = (số dự đoán đúng / tổng U) * 100%
- Output: In ra `"🥷 Attack Success Rate: XX.XX%"` rồi return ASR (float)

---

## 7. Ví Dụ Sử Dụng Toàn Bộ Module

```python
from inference_head import (
    InferenceHead, 
    sharpen, 
    mixup, 
    generate_auxiliary_labels,
    train_inference_head,
    calculate_asr
)

# Giả sử bottom_model đã train xong
bottom_model = load_bottom_model()  # ResNet-18 từ phase1
test_dataset = datasets.CIFAR10(...)

# Bước 1: Tạo X (40 nhãn mồi) và U (còn lại)
X, U = generate_auxiliary_labels(test_dataset, num_labels=40)
print(f"X: {len(X[0])} samples, U: {len(U[0])} samples")

# Bước 2: Tạo InferenceHead
inference_head = InferenceHead(embedding_dim=128, hidden_dim=256, num_classes=10)

# Bước 3: Train InferenceHead bằng MixMatch
inference_head = train_inference_head(
    bottom_model, 
    inference_head, 
    X, U, 
    epochs=50, 
    lr=0.01,
    device='cuda'
)

# Bước 4: Tính ASR
asr = calculate_asr(
    bottom_model, 
    inference_head, 
    U[0],  # ảnh
    U[1],  # labels thật
    device='cuda'
)
```

---

## 8. Yêu Cầu Chi Tiết

- Tất cả code phải có comment rõ ràng (tiếng Anh + tiếng Việt)
- Sử dụng PyTorch: `torch`, `torch.nn`, `torch.optim`, `torch.distributions`
- Có docstring cho mỗi class và hàm
- Xử lý edge case (batch size, device, ...)
- Code phải chạy được mà không lỗi
- Cung cấp **ví dụ sử dụng cụ thể** (như mục 7)
- **Hướng dẫn tích hợp** vào file `main_attack.py`:
  - Sau training chung (phase1/src/main.py) kết thúc
  - Thêm code gọi hàm từ module này để tự động chạy attack
  - In ra ASR cuối cùng

---

## 9. Kết Quả Mong Đợi

```
Epoch 1/50 - Loss_X: 0.8234, Loss_U: 0.6123, Total: 1.4357
Epoch 2/50 - Loss_X: 0.7123, Loss_U: 0.5234, Total: 1.2357
Epoch 3/50 - Loss_X: 0.6045, Loss_U: 0.4567, Total: 1.0612
...
Epoch 50/50 - Loss_X: 0.1234, Loss_U: 0.0923, Total: 0.2157

🥷 Attack Success Rate: 78.50%
🎉 BẢO ĐÃ THÀNH CÔNG ĂNCẮP DỮ LIỆU!
```

---

**LƯU Ý QUAN TRỌNG:**
- Đây là code tấn công hợp pháp cho mục đích nghiên cứu bảo mật
- Mục đích là để hiểu rõ cách hệ thống VFL có thể bị tấn công
- Không được sử dụng với ý đồ độc hại trên hệ thống thực tế

---

Sau khi AI generate code, hãy:
1. Copy code vào file: `vfl_base/phase2/src/inference_head.py`
2. Kiểm tra code chạy không lỗi
3. Tích hợp vào `main_attack.py` (copy từ phase1/src/main.py rồi thêm call hàm này)
4. Chạy `python main_attack.py` và báo cáo kết quả ASR
