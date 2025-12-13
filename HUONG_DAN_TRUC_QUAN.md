# 📊 Hướng Dẫn Sử Dụng Tính Năng Trực Quan Hóa Mới

## 🎯 Tổng Quan

Ứng dụng đã được nâng cấp với các tính năng trực quan hóa chuyên nghiệp để hỗ trợ báo cáo đồ án về tấn công Byzantine trong Federated Learning.

---

## 🆕 Tính Năng Mới

### 1. 📈 Dashboard Tổng Quan (`/dashboard`)

**Mục đích**: Cung cấp cái nhìn tổng quan về toàn bộ thí nghiệm

#### Các thành phần:

##### a) Metrics Cards
- **Total Experiments**: Tổng số thí nghiệm đã chạy
- **Avg Final Accuracy**: Độ chính xác trung bình cuối cùng
- **Avg Convergence**: Số epoch trung bình để đạt 80% accuracy
- **Attack Types**: Số loại tấn công khác nhau

##### b) Performance Heatmap
- **Ma trận màu**: Aggregators × Attack Types
- **Màu sắc**:
  - 🟢 Xanh lá: Accuracy cao (≥90%)
  - 🟡 Vàng: Accuracy trung bình (70-80%)
  - 🔴 Đỏ: Accuracy thấp (<60%)
- **Thông tin**: Hiển thị số lượng runs và accuracy trung bình

##### c) Best Performer Analysis
- Aggregator tốt nhất cho từng loại tấn công
- So sánh hiệu suất giữa các phương pháp

**Cách sử dụng cho báo cáo**:
1. Truy cập `/dashboard`
2. Chụp màn hình heatmap để thấy so sánh tổng quan
3. Sử dụng metrics cards để trích xuất số liệu thống kê
4. Best performance section để highlight kết quả tốt nhất

---

### 2. 🎭 Attack Animation Demo (`/attack-demo`)

**Mục đích**: Minh họa trực quan cách Byzantine workers tấn công

#### Tính năng chính:

##### a) Real-time Animation
- **Workers Grid**: 10 workers hiển thị theo dạng 5×2
- **Color Coding**:
  - 🔵 Xanh dương: Honest workers (với icon Shield)
  - 🔴 Đỏ: Byzantine workers (với icon Alert Triangle)
- **Animation Effects**:
  - Ring glow đỏ khi worker đang tấn công
  - Scale up effect để nhấn mạnh
  - Pulse animation cho attack action

##### b) Label Distribution Visualization
- **Original Labels**: Phân phối nhãn gốc (màu xanh)
- **Poisoned Labels**: Phân phối sau khi bị tấn công (màu đỏ)
- **Attack Arrow**: Mũi tên chỉ rõ quá trình tấn công

##### c) Attack Types
1. **Label Flipping**: 
   - 0→1, 1→0, 2→3, 3→2...
   - Tấn công đơn giản, lật nhãn sang lớp kế bên

2. **Furthest Label Flipping**:
   - 0→9, 1→8, 2→7...
   - Tấn công tinh vi hơn, lật sang lớp xa nhất

##### d) Controls
- ▶️ **Play/Pause**: Điều khiển animation
- 🔄 **Reset**: Reset về trạng thái ban đầu
- 🔀 **Switch Attack**: Chuyển đổi giữa 2 loại tấn công

**Cách sử dụng cho báo cáo**:
1. Truy cập `/attack-demo`
2. Click Play để xem animation
3. Chụp screenshot ở frame quan trọng (khi attack đang diễn ra)
4. So sánh 2 loại attack để giải thích sự khác biệt

---

### 3. 🎨 Icons/Logos Cải Tiến

**Thay đổi trong NetworkVizD3**:

#### Server Node (Parameter Server)
- **Icon mới**: Hình database/server với 3 tầng
- **Màu**: Purple (#8b5cf6)
- **Ý nghĩa**: Rõ ràng hơn vai trò là central server

#### Honest Worker
- **Icon mới**: Hình người dùng (đầu tròn + thân người)
- **Màu**: Blue (#3b82f6)
- **Ý nghĩa**: Thân thiện, đáng tin cậy

#### Byzantine Worker
- **Icon mới**: Hình tam giác cảnh báo với dấu !
- **Màu**: Red (#ef4444)
- **Ý nghĩa**: Nguy hiểm, cần cảnh giác

#### Hover Effects
- **Glow ring**: Viền sáng khi hover
- **Smooth transitions**: Chuyển đổi mượt mà
- **Tooltips**: Hiển thị thông tin chi tiết

**Lợi ích**:
- Dễ phân biệt các loại nodes
- Trực quan hơn cho presentation
- Professional hơn cho báo cáo

---

### 4. 📸 Screenshot & Export Tools

**Component**: `ScreenshotTools`

#### a) Save as PNG
- **Chất lượng**: 2× resolution (retina)
- **Format**: PNG với background trắng
- **Use case**: Screenshot nhanh cho document

#### b) Save as SVG
- **Vector format**: Scale được không giảm chất lượng
- **Use case**: LaTeX, papers, publications

#### c) Export for Presentation
- **Resolution**: 1920×1080 (Full HD)
- **Scale**: 4× (cực cao)
- **Quality**: Maximum
- **Use case**: PowerPoint, slides, posters

**Cách sử dụng**:
```tsx
import ScreenshotTools from '@/components/ScreenshotTools';

// Trong component
<div id="my-chart">
  {/* Your visualization */}
</div>

<ScreenshotTools targetId="my-chart" filename="comparison-chart" />
```

---

## 🎓 Workflow Cho Báo Cáo Đồ Án

### Bước 1: Thu thập Overview Data
1. Truy cập **Dashboard** (`/dashboard`)
2. Chụp heatmap comparison
3. Ghi lại số liệu từ metrics cards
4. Screenshot best performer section

### Bước 2: Giải thích Attack Mechanism
1. Truy cập **Attack Demo** (`/attack-demo`)
2. Chọn attack type muốn demo
3. Play animation
4. Chụp screenshot ở các frame:
   - Before attack (step 0)
   - During attack (step 3-5, khi có glow effect)
   - After attack (step 10)
5. So sánh Label Flipping vs Furthest Label

### Bước 3: Show Network Topology
1. Truy cập **Topology** (`/topology`)
2. Chọn experiment với attack
3. Play animation để thấy data flow
4. Chụp screenshot network với icons mới
5. Highlight Byzantine workers (red triangles)

### Bước 4: Compare Performance
1. Truy cập **Compare** (`/compare`)
2. Select 3-6 runs với các aggregators khác nhau
3. Cùng attack type để so sánh công bằng
4. Export accuracy chart as PNG
5. Export full data as CSV

### Bước 5: Export High-Resolution Images
1. Sử dụng **Export for Presentation** button
2. Lưu tất cả charts quan trọng ở 1920×1080
3. Import vào PowerPoint/Keynote
4. Thêm annotations và arrows

---

## 📊 Gợi Ý Sắp Xếp Slides

### Slide 1-2: Introduction
- Problem statement
- Federated Learning overview

### Slide 3: System Architecture
- Network topology từ `/topology`
- Highlight server + 10 workers
- Giải thích vai trò từng node

### Slide 4: Byzantine Attack Types
- 2 ảnh từ `/attack-demo`:
  - Label Flipping visualization
  - Furthest Label Flipping visualization
- So sánh distribution changes

### Slide 5: Attack Animation
- GIF hoặc 3-4 frames từ attack demo
- Mũi tên chỉ attack flow
- Explain impact

### Slide 6: Performance Overview
- Heatmap từ `/dashboard`
- Highlight best/worst combinations
- Color legend explanation

### Slide 7-8: Detailed Comparison
- Charts từ `/compare`
- So sánh 3-4 aggregators
- Accuracy over iterations

### Slide 9: Best Aggregator Analysis
- Best performer section từ dashboard
- Giải thích tại sao aggregator này tốt
- Trade-offs

### Slide 10: Conclusion
- Summary metrics
- Recommendations
- Future work

---

## 🎯 Tips cho Presentation

### Visual Design
- ✅ Sử dụng high-res exports (1920×1080)
- ✅ Consistent color scheme (blue=honest, red=byzantine)
- ✅ Add legends và annotations
- ✅ Keep text readable (font size ≥18pt)

### Content Flow
- ✅ Problem → Attack → Defense → Results
- ✅ Show before/after comparisons
- ✅ Use animations strategically
- ✅ Highlight key findings

### Common Mistakes to Avoid
- ❌ Low resolution screenshots
- ❌ Too much data on one slide
- ❌ Missing legends/labels
- ❌ Inconsistent color coding

---

## 🛠️ Technical Details

### Navigation Structure
```
/                    → Home page
/dashboard          → Overview metrics & heatmap
/topology           → Network visualization & animation
/compare            → Multi-run comparison
/attack-demo        → Attack animation demo
```

### Key Components
```
src/components/
  ├── DashboardPage.tsx      → Metrics cards & heatmap
  ├── AttackDemo.tsx         → Attack animation
  ├── NetworkVizD3.tsx       → D3 network (với icons mới)
  ├── ScreenshotTools.tsx    → Export functionality
  └── ui/                    → Shadcn components
```

### Dependencies Added
```json
{
  "html2canvas": "^1.4.1",
  "@types/html2canvas": "^1.0.0"
}
```

---

## 📚 LaTeX Integration

### Export CSV cho Tables
```python
# Python script để convert CSV sang LaTeX table
import pandas as pd

df = pd.read_csv('metrics.csv')
latex_table = df.to_latex(
    index=False,
    caption='Comparison of Aggregators',
    label='tab:aggregator-comparison'
)
```

### Include High-Res Images
```latex
\begin{figure}[h]
\centering
\includegraphics[width=0.9\textwidth]{heatmap_1920x1080.png}
\caption{Performance heatmap: Aggregators vs Attacks}
\label{fig:heatmap}
\end{figure}
```

---

## 🔄 Update Log

**Version 0.4.0** - December 12, 2025

### Added:
1. ✅ Dashboard page with metrics cards & heatmap
2. ✅ Attack animation demo với real-time visualization
3. ✅ Improved icons: Server (database), Honest (user), Byzantine (alert)
4. ✅ Screenshot tools với PNG/SVG export
5. ✅ High-resolution presentation export (1920×1080)
6. ✅ Navigation bar với links đến tất cả pages

### Improved:
1. ✅ NetworkVizD3 hover effects
2. ✅ Color consistency across app
3. ✅ Professional icon design
4. ✅ Better visual hierarchy

---

## 💡 Next Steps (Optional)

Nếu muốn thêm tính năng:

1. **Aggregator Visualization**: Chi tiết cách trimmed mean/FABA hoạt động
2. **Real-time Training**: WebSocket kết nối với training process
3. **3D Network**: Three.js visualization
4. **GIF Export**: Animated GIF từ attack demo
5. **PDF Report Generator**: Auto-generate PDF report

---

## 📞 Support

Nếu gặp vấn đề:
1. Check console logs: F12 → Console
2. Verify data exists in `data/SR_MNIST/`
3. Restart dev server: `npm run dev`
4. Clear cache: `rm -rf .next`

**Documentation Files**:
- `ADVANCED_FEATURES.md` - Technical details
- `TOM_TAT_NANG_CAP.md` - Vietnamese summary
- `QUICK_START.md` - Quick reference
- `HUONG_DAN_TRUC_QUAN.md` - This file

---

**Chúc bạn làm báo cáo thành công! 🎓🚀**
