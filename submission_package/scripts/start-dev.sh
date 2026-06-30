#!/bin/bash

# Script tự động khởi động dev server
# Sử dụng: npm run start-dev hoặc ./scripts/start-dev.sh

echo "🚀 Đang khởi động Federated Learning Visualizer..."

# Dọn dẹp ports (3000-3005)
echo "🧹 Dọn dẹp các port cũ..."
lsof -ti:3000,3001,3002,3003,3004,3005 2>/dev/null | xargs kill -9 2>/dev/null
sleep 1

# Xóa cache .next
if [ -d ".next" ]; then
    echo "🗑️  Xóa cache .next..."
    rm -rf .next
fi

# Khởi động server
echo "✅ Khởi động server trên http://localhost:3000"
echo ""
npm run dev
