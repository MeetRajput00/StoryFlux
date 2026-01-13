#!/bin/bash
# Quick fix script for YouTube upload limit error

echo ""
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║                                                                  ║"
echo "║          🚨 YOUTUBE UPLOAD LIMIT ERROR FIX 🚨                   ║"
echo "║                                                                  ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

echo "📊 Problem Detected:"
echo "   YouTube daily upload limit reached (6 videos/day for unverified channels)"
echo ""

echo "✅ QUICK SOLUTION (Takes 2 minutes):"
echo ""
echo "   1. Open this URL in your browser:"
echo "      👉 https://www.youtube.com/verify"
echo ""
echo "   2. Click 'Verify' and enter your phone number"
echo ""
echo "   3. Enter the verification code you receive"
echo ""
echo "   4. Done! Your upload limit increases to 100+ per day! 🎉"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "💡 WORKAROUND (While waiting for verification):"
echo ""
echo "   Create videos without uploading:"
echo "   → python3 main.py --no-upload"
echo ""
echo "   Videos are saved in: output/videos/"
echo "   Upload manually later via YouTube Studio"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "📚 For detailed information:"
echo "   → cat YOUTUBE_UPLOAD_LIMITS.md"
echo "   → or open YOUTUBE_UPLOAD_LIMITS.md in a text editor"
echo ""

echo "❓ Want to verify your channel now? (y/n)"
read -r response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Opening YouTube verification page..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open "https://www.youtube.com/verify"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        xdg-open "https://www.youtube.com/verify"
    else
        # Windows or other
        echo "Please open this URL manually: https://www.youtube.com/verify"
    fi
    echo ""
    echo "✅ Verification page opened in your browser!"
    echo "   Follow the steps to verify your channel."
    echo ""
else
    echo ""
    echo "No problem! You can verify later at: https://www.youtube.com/verify"
    echo ""
    echo "For now, use: python3 main.py --no-upload"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
