# Federated Learning Visualizer - Vercel Deployment

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/your-repo/federated-learning-visualizer)

## 🚀 Quick Deploy

1. **Push to GitHub:**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin master
```

2. **Deploy to Vercel:**
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repository
   - Vercel will auto-detect Next.js
   - Click "Deploy"

## ⚙️ Environment Variables

No environment variables needed for basic deployment!

## 📁 Data Files

The `/public/data` folder contains all experimental results:
- **Size:** ~500MB SR_MNIST dataset results
- **Note:** Vercel has 100MB function limit, but static files in `/public` are served via CDN

⚠️ **Important:** The `data/` folder is symlinked to `public/data/`. Make sure the actual data files are in `public/data/` before deploying.

## 🔧 Build Settings

Vercel will automatically use these settings (from `vercel.json`):
- **Framework:** Next.js
- **Build Command:** `npm run build`
- **Output Directory:** `.next`
- **Install Command:** `npm install`
- **Node Version:** 18.x (auto-detected)

## 🌍 Regions

Configured for Singapore region (`sin1`) for optimal performance in Asia.

## 📊 Performance

- **SSR:** Server-Side Rendering for initial page load
- **Edge Functions:** Fast data fetching
- **CDN:** Static assets served globally
- **Code Splitting:** Automatic optimization

## 🐛 Troubleshooting

### Build Fails

If build fails due to TypeScript errors:
```bash
npm run build
```
Fix errors locally first.

### Data Not Loading

Check that symlink is resolved:
```bash
ls -la public/data
```

If using Git, symlinks might not work. Copy data instead:
```bash
rm -rf public/data
cp -r data public/data
```

### Memory Issues

If build runs out of memory, add to `package.json`:
```json
"build": "NODE_OPTIONS='--max-old-space-size=4096' next build"
```

## 📝 Post-Deployment

After successful deployment:
1. Test all pages (Home, Topology, Attack Demo, Compare, Defense)
2. Verify data loads correctly
3. Check console for errors
4. Share your live URL! 🎉

## 🔗 Custom Domain

To add custom domain:
1. Go to Vercel Dashboard → Your Project → Settings → Domains
2. Add your domain
3. Update DNS records as instructed

---

Built with ❤️ for IE105 - Web Development Course
