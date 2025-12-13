# 🚀 Deploy lên Vercel - Hướng dẫn nhanh

## ✅ Đã chuẩn bị sẵn:
- ✅ Build thành công locally 
- ✅ Data đã copy vào `public/data/` (4.2MB)
- ✅ `vercel.json` config file
- ✅ Next.js 15 với output standalone
- ✅ TypeScript errors đã fix hết

## 📋 Các bước deploy:

### 1. Push code lên GitHub

```bash
# Khởi tạo git (nếu chưa có)
git init

# Add remote repository
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git

# Add và commit
git add .
git commit -m "Initial commit - FL Visualizer with DailyEng design"

# Push lên GitHub
git push -u origin master
```

### 2. Deploy trên Vercel

**Cách 1: Qua Website (Dễ nhất)**
1. Vào [vercel.com](https://vercel.com)
2. Login bằng GitHub
3. Click "New Project"
4. Import repository vừa tạo
5. Vercel tự động detect Next.js
6. Click "Deploy" ✨

**Cách 2: Qua CLI**
```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

### 3. Sau khi deploy

Vercel sẽ tự động:
- ✅ Install dependencies
- ✅ Build project (`npm run build`)
- ✅ Deploy lên CDN
- ✅ Tạo URL production: `https://your-project.vercel.app`

## 🎯 URLs sau khi deploy:

- 🏠 Homepage: `https://your-project.vercel.app/`
- 🔬 Topology: `https://your-project.vercel.app/topology`
- ⚔️ Attack Demo: `https://your-project.vercel.app/attack-demo`
- 📊 Compare: `https://your-project.vercel.app/compare`
- 🛡️ Defense: `https://your-project.vercel.app/aggregation-defense`

## 🔧 Troubleshooting

### Nếu build fails trên Vercel:

1. **Check build logs** trên Vercel Dashboard
2. **Build locally** trước: `npm run build`
3. **Fix errors** rồi push lại

### Nếu data không load:

Vercel serve static files từ `/public/` → URL `/data/...` sẽ work!

## 📈 Performance Expected:

- **Build time:** ~2-3 phút
- **Page load:** < 1s (CDN cached)
- **Lighthouse Score:** 90+ 
- **Region:** Singapore (sin1) - tối ưu cho Việt Nam

## 🎨 Features Ready:

✅ DailyEng-inspired friendly design  
✅ 4 Byzantine attack types  
✅ 5 Robust aggregators  
✅ Real SR_MNIST data (4.2MB)  
✅ Interactive visualizations  
✅ Global navigation  
✅ Responsive design  

---

**Deploy ngay để show cho thầy! 🚀**
