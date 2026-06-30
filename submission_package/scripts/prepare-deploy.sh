#!/bin/bash

# Deployment preparation script for Vercel

echo "🚀 Preparing for Vercel deployment..."

# Remove symlink
if [ -L "public/data" ]; then
    echo "📁 Removing symlink..."
    rm public/data
fi

# Copy real data
if [ -d "data" ]; then
    echo "📦 Copying data folder..."
    cp -r data public/data
    echo "✅ Data copied successfully!"
else
    echo "❌ Error: data folder not found!"
    exit 1
fi

# Check size
DATA_SIZE=$(du -sh public/data | cut -f1)
echo "📊 Data size: $DATA_SIZE"

# Create .gitignore if needed
if ! grep -q "public/data" .gitignore 2>/dev/null; then
    echo "public/data/" >> .gitignore
    echo "✅ Added public/data to .gitignore"
fi

echo ""
echo "✨ Ready to deploy!"
echo ""
echo "Next steps:"
echo "1. git add ."
echo "2. git commit -m 'Prepare for Vercel deployment'"
echo "3. git push"
echo "4. Deploy on vercel.com"
