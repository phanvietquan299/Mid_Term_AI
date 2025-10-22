# Mid-Term Pacman – Pygame GUI

Ứng dụng này cung cấp giao diện Pygame cho đồ án Pacman giữa kỳ. Phần giao diện cho phép bạn:
- tải các layout Pacman trong thư mục `pacman/layouts`
- chạy giải thuật A* với nhiều heuristic khác nhau
- chuyển sang chế độ điều khiển tay và thử nghiệm các cơ chế như teleport hoặc ăn power-up

Các mô-đun giải quyết bài toán tìm đường (A*, heuristic, môi trường Pacman) được tổ chức trong gói `pacman` và `puzzle`; phần giao diện nằm trong gói `midterm_gui`.

## Cấu trúc thư mục chính
- `run_gui.py`: entry point chạy giao diện Pygame.
- `midterm_gui/`: thành phần giao diện, quản lý sự kiện, assets và hiển thị.
- `pacman/`: mô hình Pacman, môi trường, layout và các heuristic.
- `puzzle/`: bộ thư viện tìm kiếm trạng thái tái sử dụng (A*, định nghĩa Problem/Action).
- `assets/`: hình ảnh Pacman, ghost, tường, teleport...

## Yêu cầu hệ thống
- Python 3.10 trở lên (đã kiểm tra với type hint và `__future__` annotations).
- Thư viện [`pygame`](https://www.pygame.org/news).

## Chạy nhanh Pygame
Từ thư mục dự án (`Mid_Term`), chỉ cần dùng đường dẫn tương đối:
```bash
python run_gui.py --layout pacman/layouts/maze.txt
```
Các file layout khác nằm trong `pacman/layouts/`. Nhấn `Tab` để shell tự hoàn thành tên file, không cần dán đường dẫn tuyệt đối.

## Chạy giao diện Pygame
```bash
python run_gui.py
```

Tuỳ chọn chỉ định layout khác:
```bash
python run_gui.py --layout pacman/layouts/medium_twists.txt
```

Ứng dụng mở ở chế độ toàn màn hình với tuỳ chọn `pygame.SCALED`. Nhấn `Esc` để thoát.

### Các nút điều khiển
- `Solve`: chạy A* (bắt đầu thread background). Nếu thành công, lời giải được lưu và hiện thống kê.
- `Auto`: phát lại lời giải từng bước; chỉ dùng khi đã có lời giải.
- `Step`: tiến từng bước trên lời giải.
- `Reset`: trả trạng thái về ban đầu.
- `Manual`: bật/tắt chế độ điều khiển tay.
- `H: ...`: vòng qua các heuristic khả dụng (Auto pick, ExactMST, Combined, Exact distance, Food MST, Pie aware).

### Phím nóng trong chế độ Manual
- Mũi tên hoặc `WASD`: di chuyển Pacman.
- `Space`: đứng yên.
- `T`: dịch chuyển nếu đang đứng trên ô teleport.
- `Esc`: thoát khỏi manual (nhấn thêm một lần nữa để đóng app).

Khi Auto/Manual đang chạy, bảng thông tin phía dưới sẽ đổi màu để báo trạng thái. Thông báo thời gian thực hiển thị phía trên bảng điều khiển.

## Chạy chế độ dòng lệnh (không giao diện)

Thư mục `pacman/` cung cấp một CLI nhỏ:
```bash
python -m pacman.main --layout pacman/layouts/small_basic.txt --heuristic exact-mst
```

Tùy chọn `--heuristic` nhận các giá trị: `auto`, `exact-mst`, `combo`, `exact-dist`, `mst`, `pie`, ...

## Phát triển thêm với Pygame
### Vòng đời chuẩn của một ứng dụng Pygame
1. Khởi tạo: `pygame.init()`, tạo cửa sổ, font, clock.
2. Vòng lặp chính:
   - Xử lý sự kiện bằng `pygame.event.get()`.
   - Cập nhật trạng thái trò chơi (logic, AI, hiệu ứng).
   - Vẽ khung hình mới lên surface chính.
   - `pygame.display.flip()` và `clock.tick(fps)` để giới hạn FPS.
3. Khi thoát: `pygame.quit()`.

### Tổ chức trong dự án này
- `PacmanGUI` chịu trách nhiệm cấu trúc vòng lặp chính và hiển thị.
- `SessionState` quản lý trạng thái trò chơi, lời giải, auto-play và manual.
- `InteractionController` gom toàn bộ sự kiện chuột/phím và triển khai hành động tương ứng.
- `ImageManager` nạp và co giãn assets dựa vào kích thước ô lưới.
- `ui_elements.py` định nghĩa bảng điều khiển, ticker, bảng thông tin.

Bạn có thể mở rộng giao diện bằng cách:
- thêm nút mới trong `ControlPanel` và xử lý trong `InteractionController`.
- chỉnh màu, kích thước, FPS trong `midterm_gui/ui_style.py`.
- thêm layout mới trong `pacman/layouts/` và truyền đường dẫn qua `--layout`.
- thay đổi hình ảnh trong thư mục `assets/` (giữ nguyên kích thước hình vuông để scale tốt).

## Kiểm thử nhanh
- Khi phát triển logic tìm đường, có thể chạy `python -m pacman.main` để xem thống kê cost/expanded/frontier trong terminal.
- Khi chỉnh giao diện, để debug có thể chuyển chế độ cửa sổ bằng cách sửa `pygame.display.set_mode` (ví dụ bỏ `pygame.FULLSCREEN`) trong `midterm_gui/app_window.py`.

## Điều chỉnh gameplay
- **Tốc độ xoay map**: hằng `ROTATION_PERIOD` trong `pacman/environment.py` điều khiển số bước trước khi maze quay (mặc định 30). Tăng giá trị để xoay chậm hơn.
- **Tốc độ di chuyển Auto**: chỉnh `TIMING.auto_delay` và `TIMING.fps` trong `midterm_gui/ui_style.py`. Delay nhỏ → chạy nhanh, delay lớn → chạy chậm.
- **Giao diện điều khiển**: bố cục HUD được định nghĩa ở `midterm_gui/ui_elements.py`; có thể thêm/bớt thông tin trong `InfoPanel._status_lines`.

## Gợi ý commit / triển khai
1. Thử chạy `python run_gui.py` bằng một layout nhỏ để đảm bảo pygame hoạt động.
2. Điều chỉnh tài nguyên hoặc heuristic theo nhu cầu.
3. Ghi nhận thay đổi và commit.

Chúc bạn làm việc hiệu quả với Pygame!
