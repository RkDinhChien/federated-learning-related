# 🥷 GIAI ĐOẠN 2: KẺ TẤN CÔNG XUẤT HIỆN - TOÀN CẢNH

## 🎯 Sứ Mệnh Của Bảo Tuần Này

Sau khi VFL Base System chạy thành công (**Loss ↓38%, Accuracy ↑31%**), bây giờ **Bảo** sẽ thực hiện hai cuộc tấn công để ăn cắp dữ liệu nhạy cảm từ Server (Chiến).

---

## 📋 File Hướng Dẫn

Tôi đã chuẩn bị 4 file cho bạn:

| File | Mục Đích | Hành Động |
|------|---------|----------|
| **CHI_TIET_CHO_BAO.md** | ✅ Hướng dẫn chi tiết 5 bước | **Bảo đọc file này trước tiên** |
| **GIAI_DOAN_2_HUONG_DAN.md** | 📚 Tổng quan toàn phase 2 | Đọc để hiểu mục tiêu |
| **PROMPT_1_MALICIOUS_SGD.md** | 🥷 Prompt cho AI (MaliciousSGD) | Copy-paste vào ChatGPT/Claude |
| **PROMPT_2_INFERENCE_MIXMATCH.md** | 🥷 Prompt cho AI (MixMatch) | Copy-paste vào ChatGPT/Claude |

---

## 🚀 Quy Trình Nhanh (5 Bước)

### 1️⃣ Chuẩn Bị
```bash
mkdir -p vfl_base/phase2/src
cd vfl_base/phase2
```

### 2️⃣ Tạo MaliciousSGD
- Mở **PROMPT_1_MALICIOUS_SGD.md**
- Copy-paste vào ChatGPT/Claude
- Lưu code vào `src/malicious_optimizer.py`

### 3️⃣ Tạo MixMatch Inference
- Mở **PROMPT_2_INFERENCE_MIXMATCH.md**
- Copy-paste vào ChatGPT/Claude
- Lưu code vào `src/inference_head.py`

### 4️⃣ Tạo Training Script
- Tạo `src/main_attack.py`
- Copy code từ **CHI_TIET_CHO_BAO.md** (Bước 4)

### 5️⃣ Chạy và Báo Cáo
```bash
cd src
python main_attack.py
```
- Nếu **ASR >= 75%** → Báo lại ngay!

---

## 🥷 Hai Loại Tấn Công

### Tấn Công 1: Active Attack (MaliciousSGD)
```
Bảo sửa Optimizer Client từ SGD → MaliciousSGD

Khi Training:
  Bảo's Gradient   → MaliciousSGD (thay đổi)
  Modified Gradient → Chiến nhận được
  
Kết quả:
  Chiến bị ép phụ thuộc vào dữ liệu của Bảo
  Chiến không biết mình bị tấn công
```

### Tấn Công 2: Passive Attack (MixMatch Inference)
```
Sau khi Train xong, Bảo thực hiện:
  1. Đóng băng BottomModel của Bảo
  2. Tạo InferenceHead nhỏ gắn vào
  3. Dùng 40 nhãn mồi + MixMatch
  4. Đoán nhãn của 9960 sample còn lại
  5. Tính ASR
```

---

## 📊 Mục Tiêu Chi Tiết

### Mục Tiêu 1: Chạy Thành Công
- ✅ MaliciousSGD hoạt động
- ✅ MixMatch training hội tụ
- ✅ Không có lỗi runtime

### Mục Tiêu 2: Đạt ASR >= 75%
```
Attack Success Rate = (số dự đoán đúng) / (tổng unlabeled) * 100%

Mục tiêu: >= 75%  (Ăn cắp >= 75% dữ liệu)
Tuyệt vời: >= 85% (Ăn cắp >= 85% dữ liệu)
```

---

## ⚙️ Cấu Trúc File Tạo Ra

Sau khi hoàn thành, sẽ có:

```
vfl_base/
├── phase1/                    # GIAI ĐOẠN 1 ✅ (Hoàn thành)
│   ├── src/
│   │   ├── dataset.py
│   │   ├── client_bao.py
│   │   ├── server_chien.py
│   │   └── main.py
│   ├── requirements.txt
│   └── README.md
│
└── phase2/                    # GIAI ĐOẠN 2 🚀 (Bảo đang làm)
    ├── src/
    │   ├── malicious_optimizer.py       # 🥷 MaliciousSGD
    │   ├── inference_head.py            # 🥷 MixMatch
    │   ├── main_attack.py               # 🥷 Training chính
    │   └── client_bao_attack.py         # (optional) Client sửa
    ├── docs/
    │   └── RESULTS.md                   # Kết quả báo cáo
    │
    ├── CHI_TIET_CHO_BAO.md             # ⭐ Bảo đọc đây
    ├── GIAI_DOAN_2_HUONG_DAN.md        # Tổng quan
    ├── PROMPT_1_MALICIOUS_SGD.md       # Prompt 1
    └── PROMPT_2_INFERENCE_MIXMATCH.md  # Prompt 2
```

---

## 🎓 Học Được Gì Từ Phase 2?

1. **Tấn Công Chủ Động**: Cách thao túng gradient để tấn công
2. **Tấn Công Thụ Động**: Cách sử dụng semi-supervised learning để ăn cắp
3. **MixMatch**: Thuật toán kết hợp labeled + unlabeled data
4. **VFL Vulnerability**: Điểm yếu của hệ thống VFL
5. **ASR Metric**: Cách đo lường tính hiệu quả của tấn công

---

## 🔍 Lưu Ý Quan Trọng

✅ **Này là hợp pháp vì:**
- Mục đích: Nghiên cứu bảo mật
- Bối cảnh: Giáo dục
- Phạm vi: Hệ thống test riêng (không tấn công hệ thống thực)

❌ **KHÔNG được:**
- Dùng code này để tấn công hệ thống thực
- Ăn cắp dữ liệu thực từ người khác
- Phát tán code tấn công

---

## 📞 Khi Nào Báo Lại?

**Báo lại ngay khi:**
1. ✅ Code chạy thành công (không lỗi)
2. ✅ ASR >= 75% được in ra
3. ✅ Screenshot hoặc paste output

**Báo lại với thông tin:**
- Thời gian chạy tổng cộng
- Final ASR percentage
- Số lần training epoch
- Bất cứ vấn đề nào gặp phải

---

## 🎯 Tiếp Theo (Phase 3)

Khi Bảo báo lại ASR >= 75%, tôi sẽ ném tiếp **PROMPT GIAI ĐOẠN 3:**

**FLSG (Federated Learning with Secure Gradient)** - Thuật toán phòng thủ cho Chiến
- ✅ Chiến sẽ viết code để phòng chống tấn công MaliciousSGD
- ✅ Chiến sẽ thêm defensive mechanism để bảo vệ nhãn
- ✅ So sánh: VFL bình thường vs VFL có phòng thủ

---

## 📚 Công Thức Quan Trọng

### Algorithm 1: MaliciousSGD
```
Input: Gradients g_θ, Learning rate η, β=0.9, γ=1.0, r_min, r_max
Output: Updated weights θ

v_θ = β·v_θ + (1-β)·g_θ                  # Momentum update
r_θ = 1.0 + γ·sign(v_θ ⊙ v_last)        # Amplification ratio
r_θ = clamp(r_θ, r_min, r_max)          # Constrain ratio
v_θ = r_θ·v_last                         # Apply amplification
θ = θ - η·v_θ                             # Weight update
```

### Algorithm 2: MixMatch
```
Input: Labeled set X, Unlabeled set U, Temperature T, Mixing strength α
Output: Pseudo-labels for U

p̂ = Model(U)                             # Predictions on U
ŷ_U = Sharpen(p̂, T)                      # Pseudo-labels (sharp)
λ ~ Beta(α, α)
x̃ = λ·x_X + (1-λ)·x_U                   # MixUp inputs
ỹ = λ·y_X + (1-λ)·ŷ_U                   # MixUp labels

Loss = CrossEntropy(Model(x̃_L), ỹ_L) + 
       ||SoftMax(Model(x̃_U)) - ỹ_U||_2²
```

---

## 🚀 Hãy Bắt Đầu!

**Bảo, bạn đã sẵn sàng?**

1. Đọc **CHI_TIET_CHO_BAO.md**
2. Follow 5 bước
3. Chạy `python main_attack.py`
4. Báo lại kết quả!

**Chiến, bạn tạm nghỉ tuần này!** 😎

Tuần tới, bạn sẽ viết code phòng thủ để chặn tấn công của Bảo! 🛡️

---

**Chúc bạn thành công!** 🥷💪
