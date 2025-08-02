#!/bin/bash

# XplorED Backend - View Test Reports Script
# This script displays the latest generated test reports

set -e

# Configuration
REPORT_DIR="backend/logs/endpoint_tests"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${PURPLE}🎯 $1${NC}"
}

print_subheader() {
    echo -e "${CYAN}📋 $1${NC}"
}

# Check if reports directory exists
if [ ! -d "$REPORT_DIR" ]; then
    print_error "Reports directory not found: $REPORT_DIR"
    print_info "Please run the endpoint test script first:"
    echo "   ./backend/scripts/test_all_endpoints.sh"
    exit 1
fi

# Find latest reports
LATEST_SUMMARY=$(ls -t "$REPORT_DIR"/summary_*.txt 2>/dev/null | head -1)
LATEST_MAIN=$(ls -t "$REPORT_DIR"/endpoint_test_report_*.txt 2>/dev/null | head -1)
LATEST_DETAILED=$(ls -t "$REPORT_DIR"/detailed_responses_*.json 2>/dev/null | head -1)
LATEST_BEAUTIFUL=$(ls -t "$REPORT_DIR"/beautiful_report_*.md 2>/dev/null | head -1)
LATEST_ANALYSIS=$(ls -t "$REPORT_DIR"/detailed_analysis_*.md 2>/dev/null | head -1)

echo ""
print_header "XplorED Backend - Test Reports Viewer"
echo ""

# Display available reports
print_subheader "Available Reports:"

if [ -n "$LATEST_SUMMARY" ]; then
    print_success "📊 Summary Report: $LATEST_SUMMARY"
else
    print_warning "📊 Summary Report: Not found"
fi

if [ -n "$LATEST_MAIN" ]; then
    print_success "📝 Main Report: $LATEST_MAIN"
else
    print_warning "📝 Main Report: Not found"
fi

if [ -n "$LATEST_DETAILED" ]; then
    print_success "🔍 Detailed JSON: $LATEST_DETAILED"
else
    print_warning "🔍 Detailed JSON: Not found"
fi

if [ -n "$LATEST_BEAUTIFUL" ]; then
    print_success "🎨 Beautiful Report: $LATEST_BEAUTIFUL"
else
    print_warning "🎨 Beautiful Report: Not found"
fi

if [ -n "$LATEST_ANALYSIS" ]; then
    print_success "📈 Analysis Report: $LATEST_ANALYSIS"
else
    print_warning "📈 Analysis Report: Not found"
fi

echo ""

# Ask user which report to view
print_subheader "Which report would you like to view?"
echo "1. Summary Report (Quick overview)"
echo "2. Main Report (Detailed test results)"
echo "3. Beautiful Report (Formatted markdown)"
echo "4. Analysis Report (Comprehensive analysis)"
echo "5. All Reports (View everything)"
echo "6. Generate Beautiful Report (if not exists)"
echo "7. Exit"

read -p "Enter your choice (1-7): " choice

case $choice in
    1)
        if [ -n "$LATEST_SUMMARY" ]; then
            echo ""
            print_header "📊 Summary Report"
            echo "=========================================="
            cat "$LATEST_SUMMARY"
        else
            print_error "Summary report not found"
        fi
        ;;
    2)
        if [ -n "$LATEST_MAIN" ]; then
            echo ""
            print_header "📝 Main Report"
            echo "=========================================="
            cat "$LATEST_MAIN"
        else
            print_error "Main report not found"
        fi
        ;;
    3)
        if [ -n "$LATEST_BEAUTIFUL" ]; then
            echo ""
            print_header "🎨 Beautiful Report"
            echo "=========================================="
            cat "$LATEST_BEAUTIFUL"
        else
            print_warning "Beautiful report not found. Generating one..."
            ./backend/scripts/generate_beautiful_report.sh
        fi
        ;;
    4)
        if [ -n "$LATEST_ANALYSIS" ]; then
            echo ""
            print_header "📈 Analysis Report"
            echo "=========================================="
            cat "$LATEST_ANALYSIS"
        else
            print_error "Analysis report not found"
        fi
        ;;
    5)
        echo ""
        print_header "📊 All Reports"
        echo "=========================================="

        if [ -n "$LATEST_SUMMARY" ]; then
            echo ""
            print_subheader "📊 Summary Report"
            echo "------------------------------------------"
            cat "$LATEST_SUMMARY"
        fi

        if [ -n "$LATEST_MAIN" ]; then
            echo ""
            print_subheader "📝 Main Report"
            echo "------------------------------------------"
            cat "$LATEST_MAIN"
        fi

        if [ -n "$LATEST_BEAUTIFUL" ]; then
            echo ""
            print_subheader "🎨 Beautiful Report"
            echo "------------------------------------------"
            cat "$LATEST_BEAUTIFUL"
        fi

        if [ -n "$LATEST_ANALYSIS" ]; then
            echo ""
            print_subheader "📈 Analysis Report"
            echo "------------------------------------------"
            cat "$LATEST_ANALYSIS"
        fi
        ;;
    6)
        print_info "Generating beautiful report..."
        ./backend/scripts/generate_beautiful_report.sh
        ;;
    7)
        print_info "Exiting..."
        exit 0
        ;;
    *)
        print_error "Invalid choice. Please enter a number between 1-7."
        exit 1
        ;;
esac

echo ""
print_info "Report viewing complete!"
echo ""
print_info "Additional commands:"
echo "   # View JSON with syntax highlighting"
if [ -n "$LATEST_DETAILED" ]; then
    echo "   cat $LATEST_DETAILED | jq '.'"
fi
echo "   # Open beautiful report in browser (if available)"
if [ -n "$LATEST_BEAUTIFUL" ]; then
    echo "   open $LATEST_BEAUTIFUL"
fi
echo "   # Run new endpoint tests"
echo "   ./backend/scripts/test_all_endpoints.sh"
