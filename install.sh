#!/bin/bash
set -e

echo "🚀 Installing Prisma Common..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Install prisma-common in development mode
echo "📦 Installing prisma-common in development mode..."
uv pip install -e .

echo "✅ Prisma Common installed successfully!"
echo ""
echo "📝 Next steps:"
echo "1. Copy your source files according to MIGRATION_GUIDE.md"
echo "2. Update import statements in copied files"
echo "3. Update main project dependencies"
echo "4. Test the installation"
echo ""
echo "📖 See MIGRATION_GUIDE.md for detailed instructions"
