# Dataset mê cung

`mazes.json` chứa 48 instance tự sinh bằng `src/maze.py` với seed=2026, gồm ma trận 0 (đường) và 1 (tường). Một số ô tường nối được mở ngẫu nhiên theo `loop_rate` để tạo nhiều lựa chọn đường đi. 36 instance đầu thuộc development, 12 instance cuối thuộc test. Mọi bản đồ đều có đường từ (1,1) đến (size-2,size-2). Dữ liệu tự sinh, không cần nguồn bên ngoài và có thể công khai; không có dữ liệu cá nhân. Có thể tạo lại bằng `python run_project.py`.
