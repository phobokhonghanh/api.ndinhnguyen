#!/bin/bash

# Đảm bảo thư mục logs tồn tại
mkdir -p logs

# Ghi PID của script vào file để dễ dàng dừng tiến trình
echo $$ > logs/tail.pid

# Tự động dọn dẹp các tiến trình con (như wrangler tail) khi script dừng
cleanup() {
  rm -f logs/tail.pid
  pkill -P $$ 2>/dev/null
  exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Vòng lặp vô hạn giúp tự động kết nối lại nếu wrangler tail bị ngắt kết nối
while true; do
  npx wrangler tail api --format pretty | while read -r line; do
    # Ghi log trực tiếp vào thư mục logs/ với tên file theo định dạng ngày YYYY-MM-DD
    echo "$line" >> "logs/wrangler_$(date +%Y-%m-%d).log"
  done
  
  echo "[$(date)] Wrangler tail disconnected. Reconnecting in 5 seconds..." >> "logs/wrangler_$(date +%Y-%m-%d).log"
  sleep 5
done
